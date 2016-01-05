"""
views that return HTML that is injected into pages
"""

import logging
import urllib2
from os import path
from urllib import urlencode

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, \
    HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from haystack.query import SearchQuerySet

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.forms import RightsForm
from tardis.tardis_portal.models import Experiment, DataFile, Dataset, Schema, \
    DatafileParameterSet, UserProfile
from tardis.tardis_portal.search_backend import HighlightSearchBackend
from tardis.tardis_portal.search_query import FacetFixedSearchQuery
from tardis.tardis_portal.shortcuts import return_response_error, \
    return_response_not_found, render_response_index
from tardis.tardis_portal.staging import get_full_staging_path, staging_list
from tardis.tardis_portal.util import render_public_access_badge
from tardis.tardis_portal.views.pages import ExperimentView
from tardis.tardis_portal.views.search import SearchQueryString
from tardis.tardis_portal.views.utils import _add_protocols_and_organizations

logger = logging.getLogger(__name__)


@authz.experiment_access_required
def experiment_description(request, experiment_id):
    """View an existing experiment's description. To be loaded via ajax.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param experiment_id: the ID of the experiment to be edited
    :type experiment_id: string
    :rtype: :class:`django.http.HttpResponse`

    """
    c = {}

    try:
        experiment = Experiment.safe.get(request.user, experiment_id)
    except PermissionDenied:
        return return_response_error(request)
    except Experiment.DoesNotExist:
        return return_response_not_found(request)

    c['experiment'] = experiment
    c['subtitle'] = experiment.title
    c['nav'] = [{'name': 'Data', 'link': '/experiment/view/'},
                {'name': experiment.title,
                 'link': experiment.get_absolute_url()}]

    c['authors'] = experiment.experimentauthor_set.all()

    c['datafiles'] = \
        DataFile.objects.filter(dataset__experiments=experiment_id)

    c['owners'] = experiment.get_owners()

    # calculate the sum of the datafile sizes
    c['size'] = DataFile.sum_sizes(c['datafiles'])

    c['has_download_permissions'] = \
        authz.has_experiment_download_access(request, experiment_id)

    c['has_write_permissions'] = \
        authz.has_write_permissions(request, experiment_id)

    if request.user.is_authenticated():
        c['is_owner'] = authz.has_experiment_ownership(request, experiment_id)

    _add_protocols_and_organizations(request, experiment, c)

    if 'status' in request.GET:
        c['status'] = request.GET['status']
    if 'error' in request.GET:
        c['error'] = request.GET['error']

    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/experiment_description.html', c))


@never_cache
@authz.experiment_access_required
def experiment_datasets(request, experiment_id):
    return ExperimentView.as_view()(
        request, experiment_id=experiment_id,
        template_name='tardis_portal/ajax/experiment_datasets.html')


@never_cache
@authz.experiment_access_required
def experiment_dataset_transfer(request, experiment_id):
    experiments = Experiment.safe.owned(request.user)

    def get_json_url_pattern():
        placeholder = '314159'
        return reverse('tardis.tardis_portal.views.experiment_datasets_json',
                       args=[placeholder]).replace(placeholder,
                                                   '{{experiment_id}}')

    c = {'experiments': experiments.exclude(id=experiment_id),
         'url_pattern': get_json_url_pattern()
    }
    return HttpResponse(render_response_index(
        request,
        'tardis_portal/ajax/experiment_dataset_transfer.html',
        c))


@authz.dataset_access_required
def retrieve_dataset_metadata(request, dataset_id):
    dataset = Dataset.objects.get(pk=dataset_id)
    has_write_permissions = authz.has_dataset_write(request, dataset_id)
    parametersets = dataset.datasetparameterset_set.exclude(
        schema__hidden=True)

    c = {'dataset': dataset,
         'parametersets': parametersets,
         'has_write_permissions': has_write_permissions}
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/dataset_metadata.html', c))


@never_cache
@authz.experiment_access_required
def retrieve_experiment_metadata(request, experiment_id):
    experiment = Experiment.objects.get(pk=experiment_id)
    has_write_permissions = \
        authz.has_write_permissions(request, experiment_id)
    parametersets = experiment.experimentparameterset_set\
                              .exclude(schema__hidden=True)

    c = {'experiment': experiment,
         'parametersets': parametersets,
         'has_write_permissions': has_write_permissions}
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/experiment_metadata.html', c))


@never_cache
@authz.datafile_access_required
def display_datafile_details(request, datafile_id):
    """
    Displays a box, with a list of interaction options depending on
    the file type given and displays the one with the highest priority
    first.
    Views are set up in settings. Order of list is taken as priority.
    Given URLs are called with the datafile id appended.
    """
    # retrieve valid interactions for file type
    the_file = DataFile.objects.get(id=datafile_id)
    the_schemas = [p.schema.namespace for p in the_file.getParameterSets()]
    default_view = "Datafile Metadata"
    apps = [
        (default_view, '/ajax/parameters'), ]
    if hasattr(settings, "DATAFILE_VIEWS"):
        apps += settings.DATAFILE_VIEWS

    views = []
    for ns, url in apps:
        if ns == default_view:
            views.append({"url": "%s/%s/" % (url, datafile_id),
                          "name": default_view})
        elif ns in the_schemas:
            schema = Schema.objects.get(namespace__exact=ns)
            views.append({"url": "%s/%s/" % (url, datafile_id),
                          "name": schema.name})
    context = {
        'datafile_id': datafile_id,
        'views': views,
    }
    return HttpResponse(render_response_index(
        request,
        "tardis_portal/ajax/datafile_details.html",
        context))


@never_cache
@authz.datafile_access_required
def retrieve_parameters(request, datafile_id):

    parametersets = DatafileParameterSet.objects.all()
    parametersets = parametersets.filter(datafile__pk=datafile_id)\
                                 .exclude(schema__hidden=True)

    datafile = DataFile.objects.get(id=datafile_id)
    dataset_id = datafile.dataset.id
    has_write_permissions = authz.has_dataset_write(request, dataset_id)

    c = {'parametersets': parametersets,
         'datafile': datafile,
         'has_write_permissions': has_write_permissions,
         'has_download_permissions':
         authz.has_dataset_download_access(request, dataset_id)}

    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/parameters.html', c))


@never_cache  # too complex # noqa
@authz.dataset_access_required
def retrieve_datafile_list(
        request, dataset_id,
        template_name='tardis_portal/ajax/datafile_list.html'):

    params = {}

    query = None
    highlighted_dsf_pks = []

    if 'query' in request.GET:
        search_query = FacetFixedSearchQuery(backend=HighlightSearchBackend())
        sqs = SearchQuerySet(query=search_query)
        query = SearchQueryString(request.GET['query'])
        results = sqs.raw_search(
            query.query_string() + ' AND dataset_id_stored:%i' %
            (int(dataset_id))).load_all()
        highlighted_dsf_pks = [int(r.pk) for r in results
                               if r.model_name == 'datafile' and
                               r.dataset_id_stored == int(dataset_id)]

        params['query'] = query.query_string()

    elif 'datafileResults' in request.session and 'search' in request.GET:
        highlighted_dsf_pks = [r.pk
                               for r in request.session['datafileResults']]

    dataset_results = \
        DataFile.objects.filter(
            dataset__pk=dataset_id,
        ).order_by('filename')

    if request.GET.get('limit', False) and len(highlighted_dsf_pks):
        dataset_results = dataset_results.filter(pk__in=highlighted_dsf_pks)
        params['limit'] = request.GET['limit']

    filename_search = None

    if 'filename' in request.GET and len(request.GET['filename']):
        filename_search = request.GET['filename']
        dataset_results = \
            dataset_results.filter(filename__icontains=filename_search)

        params['filename'] = filename_search

    # pagination was removed by someone in the interface but not here.
    # need to fix.
    pgresults = 100

    paginator = Paginator(dataset_results, pgresults)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.

    try:
        dataset = paginator.page(page)
    except (EmptyPage, InvalidPage):
        dataset = paginator.page(paginator.num_pages)

    is_owner = False
    has_download_permissions = authz.has_dataset_download_access(request,
                                                                 dataset_id)
    has_write_permissions = False

    if request.user.is_authenticated():
        is_owner = authz.has_dataset_ownership(request, dataset_id)
        has_write_permissions = authz.has_dataset_write(request, dataset_id)

    immutable = Dataset.objects.get(id=dataset_id).immutable

    c = {
        'datafiles': dataset,
        'paginator': paginator,
        'immutable': immutable,
        'dataset': Dataset.objects.get(id=dataset_id),
        'filename_search': filename_search,
        'is_owner': is_owner,
        'highlighted_datafiles': highlighted_dsf_pks,
        'has_download_permissions': has_download_permissions,
        'has_write_permissions': has_write_permissions,
        'search_query': query,
        'params': urlencode(params),
    }
    _add_protocols_and_organizations(request, None, c)
    return HttpResponse(render_response_index(request, template_name, c))


@authz.dataset_write_permissions_required
def import_staging_files(request, dataset_id):
    """
    Creates an jstree view of the staging area of the user, and provides
    a selection mechanism importing files.
    """

    staging = get_full_staging_path(request.user.username)
    if not staging:
        return HttpResponseNotFound()

    c = {
        'dataset_id': dataset_id,
        'staging_mount_prefix': settings.STAGING_MOUNT_PREFIX,
        'staging_mount_user_suffix_enable':
        settings.STAGING_MOUNT_USER_SUFFIX_ENABLE,
    }
    return HttpResponse(
        render(request, 'tardis_portal/ajax/import_staging_files.html', c))


def list_staging_files(request, dataset_id):
    """
    Creates an jstree view of the staging area of the user, and provides
    a selection mechanism importing files.
    """

    staging = get_full_staging_path(request.user.username)
    if not staging:
        return HttpResponseNotFound()

    from_path = staging
    root = False
    try:
        path_var = request.GET.get('path', '')
        if not path_var:
            root = True
        from_path = path.join(staging, urllib2.unquote(path_var))
    except ValueError:
        from_path = staging

    c = {
        'dataset_id': dataset_id,
        'directory_listing': staging_list(from_path, staging, root=root),
    }
    return HttpResponse(render(
        request, 'tardis_portal/ajax/list_staging_files.html', c))


def experiment_public_access_badge(request, experiment_id):
    try:
        experiment = Experiment.objects.get(id=experiment_id)
    except Experiment.DoesNotExist:
        HttpResponse('')

    if authz.has_experiment_access(request, experiment_id):
        return HttpResponse(render_public_access_badge(experiment))
    else:
        return HttpResponse('')


@authz.experiment_ownership_required
def choose_rights(request, experiment_id):
    '''
    Choose access rights and licence.
    '''
    experiment = Experiment.objects.get(id=experiment_id)

    def is_valid_owner(owner):
        if not settings.REQUIRE_VALID_PUBLIC_CONTACTS:
            return True

        userProfile, created = UserProfile.objects.get_or_create(
            user=owner)

        return userProfile.isValidPublicContact()

    # Forbid access if no valid owner is available (and show error message)
    if not any([is_valid_owner(owner) for owner in experiment.get_owners()]):
        c = {'no_valid_owner': True, 'experiment': experiment}
        return HttpResponseForbidden(render_response_index(
            request,
            'tardis_portal/ajax/unable_to_choose_rights.html', c))

    # Process form or prepopulate it
    if request.method == 'POST':
        form = RightsForm(request.POST)
        if form.is_valid():
            experiment.public_access = form.cleaned_data['public_access']
            experiment.license = form.cleaned_data['license']
            experiment.save()
    else:
        form = RightsForm({'public_access': experiment.public_access,
                           'license': experiment.license_id})

    c = {'form': form, 'experiment': experiment}
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/choose_rights.html', c))
