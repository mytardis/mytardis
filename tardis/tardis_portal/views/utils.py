"""
helper functions used by other views
"""

import json
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template.defaultfilters import filesizeformat

from tardis.tardis_portal import constants
from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.errors import UnsupportedSearchQueryTypeError
from tardis.tardis_portal.forms import MXDatafileSearchForm, \
    createSearchDatafileForm, \
    createSearchExperimentForm
from tardis.tardis_portal.models import Schema, ParameterName
from tardis.tardis_portal.shortcuts import render_response_search

logger = logging.getLogger(__name__)


def _redirect_303(*args, **kwargs):
    response = redirect(*args, **kwargs)
    response.status_code = 303
    return response


def _add_protocols_and_organizations(request, collection_object, c):
    """Add the protocol, format and organization details for
    archive requests.  Since the MacOSX archiver can't cope with
    streaming ZIP, the best way to avoid 'user disappointment'
    is to not offer ZIP."""

    if getattr(settings, 'USER_AGENT_SENSING', False) and \
            request.user_agent:
        logger.debug('user_agent.os.family: %s' % request.user_agent.os.family)
        cannot_do_zip = request.user_agent.os.family in ['Macintosh',
                                                         'Mac OS X']
    else:
        cannot_do_zip = False

    if collection_object:
        c['protocol'] = []
        download_urls = collection_object.get_download_urls()
        for key, value in download_urls.iteritems():
            if cannot_do_zip and key == 'zip':
                continue
            c['protocol'] += [[key, value]]

    formats = getattr(settings, 'DEFAULT_ARCHIVE_FORMATS', ['tgz', 'tar'])
    c['default_format'] = filter(
        lambda x: not (cannot_do_zip and x == 'zip'), formats)[0]

    from tardis.tardis_portal.download import get_download_organizations
    c['organization'] = get_download_organizations()
    c['default_organization'] = getattr(
        settings, 'DEFAULT_ARCHIVE_ORGANIZATION', 'classic')


def __getFilteredDatafiles(request, searchQueryType, searchFilterData):
    """Filter the list of datafiles for the provided searchQueryType using the
    cleaned up searchFilterData.

    Arguments:
    request -- the HTTP request
    searchQueryType -- the type of query, 'mx' or 'saxs'
    searchFilterData -- the cleaned up search form data

    Returns:
    A list of datafiles as a result of the query or None if the provided search
      request is invalid

    """

    datafile_results = authz.get_accessible_datafiles_for_user(request)
    logger.info('__getFilteredDatafiles: searchFilterData {0}'.
                format(searchFilterData))

    # there's no need to do any filtering if we didn't find any
    # datafiles that the user has access to
    if not datafile_results:
        logger.info("""__getFilteredDatafiles: user {0} doesn\'t have
                    access to any experiments""".format(request.user))
        return datafile_results

    q = {
        'datafileparameterset__datafileparameter__name__schema__namespace__in':
        Schema.getNamespaces(Schema.DATAFILE, searchQueryType)
    }
    datafile_results = datafile_results.filter(**q).distinct()

    # if filename is searchable which i think will always be the case...
    if searchFilterData['filename'] != '':
        datafile_results = \
            datafile_results.filter(
                filename__icontains=searchFilterData['filename'])
    # TODO: might need to cache the result of this later on

    # get all the datafile parameters for the given schema
    parameters = [p for p in
                  ParameterName.objects.filter(
                      schema__namespace__in=Schema.getNamespaces(
                          Schema.DATAFILE, searchQueryType))]

    datafile_results = __filterParameters(
        parameters, datafile_results,
        searchFilterData, 'datafileparameterset__datafileparameter')

    # get all the dataset parameters for given schema
    parameters = [p for p in
                  ParameterName.objects.filter(
                      schema__namespace__in=Schema.getNamespaces(
                          Schema.DATASET, searchQueryType))]

    datafile_results = __filterParameters(
        parameters, datafile_results,
        searchFilterData, 'dataset__datasetparameterset__datasetparameter')

    # let's sort it in the end

    if datafile_results:
        datafile_results = datafile_results.order_by('filename')
    logger.debug("results: {0}".format(datafile_results))
    return datafile_results


def __getFilteredExperiments(request, searchFilterData):
    """Filter the list of experiments using the cleaned up searchFilterData.

    Arguments:
    request -- the HTTP request
    searchFilterData -- the cleaned up search experiment form data

    Returns:
    A list of experiments as a result of the query or None if the provided
      search request is invalid

    """

    experiments = authz.get_accessible_experiments(request)

    if experiments is None:
        return []

    # search for the default experiment fields
    if searchFilterData['title'] != '':
        experiments = \
            experiments.filter(title__icontains=searchFilterData['title'])

    if searchFilterData['description'] != '':
        experiments = \
            experiments.filter(
                description__icontains=searchFilterData['description'])

    if searchFilterData['institutionName'] != '':
        experiments = experiments.filter(
            institution_name__icontains=searchFilterData['institutionName'])

    if searchFilterData['creator'] != '':
        experiments = experiments.filter(
            experimentauthor__author__icontains=searchFilterData['creator'])

    date = searchFilterData['date']
    if date is not None:
        experiments = \
            experiments.filter(start_time__lt=date, end_time__gt=date)

    # get all the experiment parameters
    exp_schema_namespaces = Schema.getNamespaces(Schema.EXPERIMENT)
    parameters = ParameterName.objects.filter(
        schema__namespace__in=exp_schema_namespaces, is_searchable=True)

    experiments = __filterParameters(
        parameters, experiments,
        searchFilterData, 'experimentparameterset__experimentparameter')

    # let's sort it in the end
    experiments = experiments.order_by('title')

    return experiments


def __filterParameters(parameters, datafile_results,  # too complex # noqa
                       searchFilterData, paramType):
    """Go through each parameter and apply it as a filter (together with its
    specified comparator) on the provided list of datafiles.

    :param parameters: list of ParameterNames model
    :type parameters: list containing
       :py:class:`tardis.tardis_portal.models.ParameterNames`
    :param datafile_results: list of datafile to apply the filter
    :param searchFilterData: the cleaned up search form data
    :param paramType: either ``datafile`` or ``dataset``
    :type paramType: :py:class:`tardis.tardis_portal.models.Dataset` or
       :py:class:`tardis.tardis_portal.models.DataFile`

    :returns: A list of datafiles as a result of the query or None if the
      provided search request is invalid

    """

    for parameter in parameters:
        fieldName = parameter.getUniqueShortName()
        kwargs = {paramType + '__name__id': parameter.id}
        try:

            # if parameter is a string...
            if not parameter.data_type == ParameterName.NUMERIC:
                if searchFilterData[fieldName] != '':
                    # let's check if this is a field that's specified to be
                    # displayed as a dropdown menu in the form
                    if parameter.choices != '':
                        if searchFilterData[fieldName] != '-':
                            kwargs[paramType + '__string_value__iexact'] = \
                                searchFilterData[fieldName]
                    else:
                        if parameter.comparison_type == \
                                ParameterName.EXACT_VALUE_COMPARISON:
                            kwargs[paramType + '__string_value__iexact'] = \
                                searchFilterData[fieldName]
                        elif parameter.comparison_type == \
                                ParameterName.CONTAINS_COMPARISON:
                            # we'll implement exact comparison as 'icontains'
                            # for now
                            kwargs[paramType + '__string_value__icontains'] = \
                                searchFilterData[fieldName]
                        else:
                            # if comparison_type on a string is a comparison
                            # type that can only be applied to a numeric value,
                            # we'll default to just using 'icontains'
                            # comparison
                            kwargs[paramType + '__string_value__icontains'] = \
                                searchFilterData[fieldName]
                else:
                    pass
            else:  # parameter.isNumeric():
                if parameter.comparison_type == \
                        ParameterName.RANGE_COMPARISON:
                    fromParam = searchFilterData[fieldName + 'From']
                    toParam = searchFilterData[fieldName + 'To']
                    if fromParam is None and toParam is None:
                        pass
                    else:
                        # if parameters are provided and we want to do a range
                        # comparison
                        # note that we're using '1' as the lower range as using
                        # '0' in the filter would return all the data
                        # TODO: investigate on why the oddness above is
                        #       happening
                        # TODO: we should probably move the static value here
                        #       to the constants module
                        kwargs[paramType + '__numerical_value__range'] = \
                            (fromParam is None and
                             constants.FORM_RANGE_LOWEST_NUM or fromParam,
                             toParam is not None and toParam or
                             constants.FORM_RANGE_HIGHEST_NUM)

                elif searchFilterData[fieldName] is not None:

                    # if parameter is an number and we want to handle other
                    # type of number comparisons
                    if parameter.comparison_type == \
                            ParameterName.EXACT_VALUE_COMPARISON:
                        kwargs[paramType + '__numerical_value__exact'] = \
                            searchFilterData[fieldName]

                    # TODO: is this really how not equal should be declared?
                    # elif parameter.comparison_type ==
                    #       ParameterName.NOT_EQUAL_COMPARISON:
                    #   datafile_results = \
                    #       datafile_results.filter(
                    #  datafileparameter__name__name__icontains=parameter.name)
                    #       .filter(
                    #  ~Q(datafileparameter__numerical_value=searchFilterData[
                    #       parameter.name]))

                    elif parameter.comparison_type == \
                            ParameterName.GREATER_THAN_COMPARISON:
                        kwargs[paramType + '__numerical_value__gt'] = \
                            searchFilterData[fieldName]
                    elif parameter.comparison_type == \
                            ParameterName.GREATER_THAN_EQUAL_COMPARISON:
                        kwargs[paramType + '__numerical_value__gte'] = \
                            searchFilterData[fieldName]
                    elif parameter.comparison_type == \
                            ParameterName.LESS_THAN_COMPARISON:
                        kwargs[paramType + '__numerical_value__lt'] = \
                            searchFilterData[fieldName]
                    elif parameter.comparison_type == \
                            ParameterName.LESS_THAN_EQUAL_COMPARISON:
                        kwargs[paramType + '__numerical_value__lte'] = \
                            searchFilterData[fieldName]
                    else:
                        # if comparison_type on a numeric is a comparison type
                        # that can only be applied to a string value, we'll
                        # default to just using 'exact' comparison
                        kwargs[paramType + '__numerical_value__exact'] = \
                            searchFilterData[fieldName]
                else:
                    # ignore...
                    pass

            # we will only update datafile_results if we have an additional
            # filter (based on the 'passed' condition) in addition to the
            # initial value of kwargs
            if len(kwargs) > 1:
                logger.debug(kwargs)
                datafile_results = datafile_results.filter(**kwargs)
        except KeyError:
            pass

    return datafile_results


def __forwardToSearchDatafileFormPage(request, searchQueryType,
                                      searchForm=None):
    """Forward to the search data file form page."""

    # TODO: remove this later on when we have a more generic search form
    if searchQueryType == 'mx':
        url = 'tardis_portal/search_datafile_form_mx.html'
        searchForm = MXDatafileSearchForm()
        c = {'header': 'Search Datafile',
             'searchForm': searchForm}
        return HttpResponse(render_response_search(request, url, c))

    url = 'tardis_portal/search_datafile_form.html'
    if not searchForm:
        # if searchQueryType == 'saxs':
        SearchDatafileForm = createSearchDatafileForm(searchQueryType)
        searchForm = SearchDatafileForm()
        # else:
        #    # TODO: what do we need to do if the user didn't provide a page to
        #            display?
        #    pass

    from itertools import groupby

    # sort the fields in the form as it will make grouping the related fields
    # together in the next step easier
    sortedSearchForm = sorted(searchForm, lambda x, y: cmp(x.name, y.name))

    # modifiedSearchForm will be used to customise how the range type of fields
    # will be displayed. range type of fields will be displayed side by side.
    modifiedSearchForm = [list(g) for k, g in groupby(
        sortedSearchForm, lambda x: x.name.rsplit('To')[0].rsplit('From')[0])]

    # the searchForm will be used by custom written templates whereas the
    # modifiedSearchForm will be used by the 'generic template' that the
    # dynamic search datafiles form uses.
    c = {'header': 'Search Datafile',
         'searchForm': searchForm,
         'modifiedSearchForm': modifiedSearchForm}
    return HttpResponse(render_response_search(request, url, c))


def __forwardToSearchExperimentFormPage(request):
    """Forward to the search experiment form page."""

    searchForm = __getSearchExperimentForm(request)

    c = {'searchForm': searchForm}
    url = 'tardis_portal/search_experiment_form.html'
    return HttpResponse(render_response_search(request, url, c))


def __getSearchDatafileForm(request, searchQueryType):
    """Create the search datafile form based on the HTTP GET request.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param searchQueryType: The search query type: 'mx' or 'saxs'
    :raises:
       :py:class:`tardis.tardis_portal.errors.UnsupportedSearchQueryTypeError`
       is the provided searchQueryType is not supported.
    :returns: The supported search datafile form

    """

    try:
        SearchDatafileForm = createSearchDatafileForm(searchQueryType)
        form = SearchDatafileForm(request.GET)
        return form
    except UnsupportedSearchQueryTypeError, e:
        raise e


def __getSearchExperimentForm(request):
    """Create the search experiment form.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :returns: The search experiment form.

    """

    SearchExperimentForm = createSearchExperimentForm()
    form = SearchExperimentForm(request.GET)
    return form


def __processDatafileParameters(request, searchQueryType, form):
    """Validate the provided datafile search request and return search results.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param searchQueryType: The search query type
    :param form: The search form to use
    :raises:
       :py:class:`tardis.tardis_portal.errors.SearchQueryTypeUnprovidedError`
       if searchQueryType is not in the HTTP GET request
    :raises:
       :py:class:`tardis.tardis_portal.errors.UnsupportedSearchQueryTypeError`
       is the provided searchQueryType is not supported
    :returns: A list of datafiles as a result of the query or None if the
       provided search request is invalid.
    :rtype: list of :py:class:`tardis.tardis_portal.models.DataFiles` or
       None

    """

    if form.is_valid():

        datafile_results = __getFilteredDatafiles(
            request, searchQueryType, form.cleaned_data)

        # let's cache the query with all the filters in the session so
        # we won't have to keep running the query all the time it is needed
        # by the paginator
        request.session['datafileResults'] = datafile_results
        return datafile_results
    else:
        return None


def __processExperimentParameters(request, form):
    """Validate the provided experiment search request and return search
    results.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param form: The search form to use
    :returns: A list of experiments as a result of the query or None if the
      provided search request is invalid.

    """

    if form.is_valid():
        experiments = __getFilteredExperiments(request, form.cleaned_data)
        # let's cache the query with all the filters in the session so
        # we won't have to keep running the query all the time it is needed
        # by the paginator
        request.session['experiments'] = experiments
        return experiments
    else:
        return None


def get_dataset_info(dataset, include_thumbnail=False, exclude=None):  # too complex # noqa
    obj = model_to_dict(dataset)
    if exclude is None or 'datafiles' not in exclude or 'file_count' \
       not in exclude:
        datafiles = list(
            dataset.datafile_set.values_list('id', flat=True))
        if exclude is None or 'datafiles' not in exclude:
            obj['datafiles'] = datafiles
        if exclude is None or 'file_count' not in exclude:
            obj['file_count'] = len(datafiles)

    obj['url'] = dataset.get_absolute_url()

    if exclude is None or 'size' not in exclude:
        obj['size'] = dataset.get_size()
        obj['size_human_readable'] = filesizeformat(obj['size'])

    if include_thumbnail:
        try:
            obj['thumbnail'] = reverse(
                'tardis.tardis_portal.views.dataset_thumbnail',
                kwargs={'dataset_id': dataset.id})
        except AttributeError:
            pass

    if exclude is None or 'datasettype' not in exclude:
        if hasattr(settings, "DATASET_VIEWS"):
            schemas = {}
            for ps in dataset.getParameterSets():
                schemas[ps.schema.namespace] = ps.schema
            for ns, view_fn in settings.DATASET_VIEWS:
                if ns in schemas:
                    obj["datasettype"] = schemas[ns].name
                    break
    return obj


def remove_csrf_token(request):
    '''
    rather than fixing the form code that loops over all POST entries
    indiscriminately, I am removing the csrf token with this hack.
    This is only required in certain form code and can be removed should
    this ever be fixed
    '''
    new_post_dict = request.POST.copy()
    del(new_post_dict['csrfmiddlewaretoken'])
    request.POST = new_post_dict
    return request


class HttpResponseMethodNotAllowed(HttpResponse):
    status_code = 303

    def __init__(self, *args, **kwargs):
        super(HttpResponseMethodNotAllowed, self).__init__(*args, **kwargs)
        try:
            self["Allow"] = kwargs['allow']
        except:
            self["Allow"] = 'GET'


class HttpResponseSeeAlso(HttpResponseRedirect):
    status_code = 303


def feedback(request):
    if request.method == 'POST':
        feedback_data = json.loads(request.POST['data'])
        message = feedback_data[0]['Issue']
        img_base64 = feedback_data[1]
        img = img_base64.replace('data:image/png;base64,', '').decode('base64')
        admin_emails = [v for k, v in settings.ADMINS]
        email = EmailMessage('[TARDIS] User feedback', message,
                             'store.star.help@monash.edu', admin_emails)
        email.attach('screenshot.png', img, 'image/png')
        email.send()
        return HttpResponse('OK')
    else:
        return redirect('/')
