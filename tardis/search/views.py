"""
views relevant to search
"""
import logging
import warnings

from django.contrib.auth.models import User
from django.http import HttpResponse
from haystack.generic_views import SearchView

from tardis.search.forms import GroupedSearchForm
from tardis.search.utils import SearchQueryString
from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.deprecations import RemovedInMyTardis311Warning
from tardis.tardis_portal.forms import createSearchDatafileSelectionForm
from tardis.tardis_portal.hacks import oracle_dbops_hack
from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.shortcuts import render_response_search, \
    render_response_index
from tardis.tardis_portal.views.utils import __forwardToSearchExperimentFormPage, \
    __getSearchExperimentForm, __processExperimentParameters, \
    __getSearchDatafileForm, __processDatafileParameters, \
    __forwardToSearchDatafileFormPage

logger = logging.getLogger(__name__)


def getNewSearchDatafileSelectionForm(initial=None):
    DatafileSelectionForm = createSearchDatafileSelectionForm(initial)
    return DatafileSelectionForm()


@oracle_dbops_hack
def search_experiment(request):

    """Either show the search experiment form or the result of the search
    experiment query.

    """

    if not request.GET:
        return __forwardToSearchExperimentFormPage(request)

    form = __getSearchExperimentForm(request)
    experiments = __processExperimentParameters(request, form)

    # check if the submitted form is valid
    if experiments is not None:
        bodyclass = 'list'
    else:
        return __forwardToSearchExperimentFormPage(request)

    # remove information from previous searches from session
    if 'datafileResults' in request.session:
        del request.session['datafileResults']

    results = []
    for e in experiments:
        result = {}
        result['sr'] = e
        result['dataset_hit'] = False
        result['datafile_hit'] = False
        result['experiment_hit'] = True
        results.append(result)
    c = {'header': 'Search Experiment',
         'experiments': results,
         'bodyclass': bodyclass}
    url = 'tardis_portal/search_experiment_results.html'
    return render_response_search(request, url, c)


def search_quick(request):
    get = False
    experiments = Experiment.objects.all().order_by('title')

    if 'results' in request.GET:
        get = True
        if 'quicksearch' in request.GET and request.GET['quicksearch']:
            experiments = \
                experiments.filter(
                    title__icontains=request.GET['quicksearch']) | \
                experiments.filter(
                    institution_name__icontains=request.GET['quicksearch']) | \
                experiments.filter(
                    experimentauthor__author__name__icontains=request.GET[
                        'quicksearch']) | \
                experiments.filter(
                    pdbid__pdbid__icontains=request.GET['quicksearch'])

            experiments = experiments.distinct()

            logger.debug(experiments)

    c = {'submitted': get, 'experiments': experiments,
         'subtitle': 'Search Experiments'}
    return render_response_index(
        request, 'tardis_portal/search_experiment.html', c)


def search_datafile(request):  # too complex # noqa
    """Either show the search datafile form or the result of the search
    datafile query.

    """
    warnings.warn(
        "The old DataFile search form (triggered by the /search/datafile/ "
        "URL) was only useful for X-Ray Diffraction data.  It needs to be "
        "rewritten if it is to be useful for other data types.",
        RemovedInMyTardis311Warning
    )
    if 'type' in request.GET:
        searchQueryType = request.GET.get('type')
    else:
        # for now we'll default to MX if nothing is provided
        # TODO: should we forward the page to experiment search page if
        #       nothing is provided in the future?
        searchQueryType = 'mx'
    logger.info('search_datafile: searchQueryType {0}'.format(searchQueryType))
    # TODO: check if going to /search/datafile will flag an error in unit test
    bodyclass = None

    if 'page' not in request.GET and 'type' in request.GET and \
            len(request.GET) > 1:
        # display the 1st page of the results

        form = __getSearchDatafileForm(request, searchQueryType)
        datafile_results = __processDatafileParameters(
            request, searchQueryType, form)
        if datafile_results is not None:
            bodyclass = 'list'
        else:
            return __forwardToSearchDatafileFormPage(
                request, searchQueryType, form)

    else:
        if 'page' in request.GET:
            # succeeding pages of pagination
            if 'datafileResults' in request.session:
                datafile_results = request.session['datafileResults']
            else:
                form = __getSearchDatafileForm(request, searchQueryType)
                datafile_results = __processDatafileParameters(
                    request, searchQueryType, form)
                if datafile_results is not None:
                    bodyclass = 'list'
                else:
                    return __forwardToSearchDatafileFormPage(
                        request, searchQueryType, form)
        else:
            # display the form
            if 'datafileResults' in request.session:
                del request.session['datafileResults']
            return __forwardToSearchDatafileFormPage(request, searchQueryType)

    # process the files to be displayed by the paginator...
    # paginator = Paginator(datafile_results,
    #                      constants.DATAFILE_RESULTS_PER_PAGE)

    # try:
    #    page = int(request.GET.get('page', '1'))
    # except ValueError:
    #    page = 1

    # If page request (9999) is out of :range, deliver last page of results.
    # try:
    #    datafiles = paginator.page(page)
    # except (EmptyPage, InvalidPage):
    #    datafiles = paginator.page(paginator.num_pages)

    import re
    cleanedUpQueryString = re.sub('&page=\d+', '',
                                  request.META['QUERY_STRING'])

    # get experiments associated with datafiles
    if datafile_results:
        experiment_pks = list(set(datafile_results.values_list(
            'dataset__experiments', flat=True)))
        experiments = Experiment.safe.in_bulk(experiment_pks)
    else:
        experiments = {}

    results = []
    for key, e in experiments.items():
        result = {}
        result['sr'] = e
        result['dataset_hit'] = False
        result['datafile_hit'] = True
        result['experiment_hit'] = False
        results.append(result)

    c = {
        'experiments': results,
        'datafiles': datafile_results,
        # 'paginator': paginator,
        'query_string': cleanedUpQueryString,
        'subtitle': 'Search Datafiles',
        'nav': [{'name': 'Search Datafile', 'link': '/search/datafile/'}],
        'bodyclass': bodyclass,
        'search_pressed': True,
        'searchDatafileSelectionForm': getNewSearchDatafileSelectionForm()}
    url = 'tardis_portal/search_experiment_results.html'
    return render_response_search(request, url, c)


class ExperimentSearchView(SearchView):
    def __name__(self):
        return "ExperimentSearchView"

    def extra_context(self):
        extra = super(ExperimentSearchView, self).extra_context()
        # Results may contain Experiments, Datasets and DataFiles.
        # Group them into experiments, noting whether or not the search
        # hits were in the Dataset(s) or DataFile(s)
        results = self.results
        facets = results.facet_counts()
        if facets:
            experiment_facets = facets['fields']['experiment_id_stored']
            experiment_ids = [int(f[0])
                              for f in experiment_facets if int(f[1]) > 0]
        else:
            experiment_ids = []

        access_list = []

        if self.request.user.is_authenticated():
            access_list.extend(
                [e.pk for e in
                 authz.get_accessible_experiments(self.request)])

        access_list.extend(
            [e.pk for e in Experiment.objects
                .exclude(public_access=Experiment.PUBLIC_ACCESS_NONE)
                .exclude(public_access=Experiment.PUBLIC_ACCESS_EMBARGO)])

        ids = list(set(experiment_ids) & set(access_list))
        experiments = Experiment.objects.filter(pk__in=ids)\
                                        .order_by('-update_time')

        results = []
        for e in experiments:
            result = {'sr': e, 'dataset_hit': False, 'datafile_hit': False,
                      'experiment_hit': False}
            results.append(result)

        extra['experiments'] = results
        return extra

    # override SearchView's method in order to
    # return a ResponseContext
    def create_response(self):
        (paginator, page) = self.build_page()

        # Remove unnecessary whitespace
        # TODO this should just be done in the form clean...
        query = SearchQueryString(self.query)
        context = {
            'search_query': query,
            'form': self.form,
            'page': page,
            'paginator': paginator,
        }
        context.update(self.extra_context())

        return render_response_index(self.request, self.template, context)


def retrieve_field_list(request):

    from tardis.search.search_indexes import DataFileIndex

    # Get all of the fields in the indexes
    #
    # TODO: these should be onl read from registered indexes
    #
    allFields = DataFileIndex.fields.items()

    users = User.objects.all()

    usernames = [u.first_name + ' ' + u.last_name + ':username' for u in users]

    # Collect all of the indexed (searchable) fields, except
    # for the main search document ('text')
    searchableFields = ([key + ':search_field' for key, f in allFields
                         if f.indexed is True and key != 'text'])

    auto_list = usernames + searchableFields

    fieldList = '+'.join([str(fn) for fn in auto_list])
    return HttpResponse(fieldList)


class SingleSearchView(SearchView):
    form_class = GroupedSearchForm
    template_name = 'search/search.html'

    def form_valid(self, form):
        sqs = form.search(user=self.request.user)
        context = self.get_context_data(**{
            self.form_name: form,
            'query': form.cleaned_data.get(self.search_field),
            'object_list': sqs,
        })
        return self.render_to_response(context)
