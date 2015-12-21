"""
views that render full pages
"""

import logging
import re
import sys
from os import path

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.db import connection
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_page

from tardis.apps.push_to.apps import PushToConfig
from tardis.apps.push_to.views import (
    initiate_push_experiment, initiate_push_dataset)
from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.auth.decorators import (
    has_experiment_download_access, has_experiment_write, has_dataset_write)
from tardis.tardis_portal.auth.localdb_auth import django_user
from tardis.tardis_portal.forms import ExperimentForm, DatasetForm
from tardis.tardis_portal.models import Experiment, Dataset, DataFile, ObjectACL
from tardis.tardis_portal.shortcuts import render_response_index, \
    return_response_error, return_response_not_found, get_experiment_referer, \
    render_response_search
from tardis.tardis_portal.util import dirname_with_id
from tardis.tardis_portal.views.search import SearchQueryString
from tardis.tardis_portal.views.utils import (
    _redirect_303, _add_protocols_and_organizations, HttpResponseSeeAlso)

logger = logging.getLogger(__name__)


def index(request):
    status = ''
    limit = 8
    c = {'status': status}
    if request.user.is_authenticated():
        private_experiments = Experiment.safe.owned_and_shared(request.user)\
            .order_by('-update_time')[:limit]
        c['private_experiments'] = private_experiments
        if len(private_experiments) > 4:
            limit = 4
    public_experiments = Experiment.objects\
        .exclude(public_access=Experiment.PUBLIC_ACCESS_NONE)\
        .exclude(public_access=Experiment.PUBLIC_ACCESS_EMBARGO)\
        .order_by('-update_time')[:limit]
    c['public_experiments'] = public_experiments
    c['DEFAULT_LOGIN'] = settings.DEFAULT_LOGIN
    c['RAPID_CONNECT_ENABLED'] = settings.RAPID_CONNECT_ENABLED
    c['RAPID_CONNECT_LOGIN_URL'] = settings.RAPID_CONNECT_CONFIG[
        'authnrequest_url']
    c['CAS_ENABLED'] = settings.CAS_ENABLED
    return HttpResponse(render_response_index(request,
                        'tardis_portal/index.html', c))


def about(request):

    c = {'subtitle': 'About',
         'about_pressed': True,
         'nav': [{'name': 'About', 'link': '/about/'}],
         'version': settings.MYTARDIS_VERSION,
         'custom_about_section': getattr(
             settings, 'CUSTOM_ABOUT_SECTION_TEMPLATE',
             'tardis_portal/about_include.html'),
         }
    return HttpResponse(render_response_index(request,
                        'tardis_portal/about.html', c))


@login_required
def my_data(request):
    '''
    show data with credential-based access
    delegate to custom views depending on settings
    '''

    c = {
        'owned_experiments': Experiment.safe.owned(request.user)
        .order_by('-update_time'),
        'shared_experiments': Experiment.safe.shared(request.user)
        .order_by('-update_time'),
    }
    return HttpResponse(render_response_index(
        request, 'tardis_portal/my_data.html', c))


@authz.experiment_access_required  # too complex # noqa
def view_experiment(request, experiment_id,
                    template_name='tardis_portal/view_experiment.html'):

    """View an existing experiment.

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

    if hasattr(settings, "EXPERIMENT_VIEWS"):
        namespaces = [ps.schema.namespace
                      for ps in experiment.getParameterSets()]
        for ns, view_fn in settings.EXPERIMENT_VIEWS:
            ns_match = next((n for n in namespaces if re.match(ns, n)), None)
            if ns_match:
                x = view_fn.split(".")
                mod_name, fn_name = (".".join(x[:-1]), x[-1])
                try:
                    module = __import__(mod_name, fromlist=[fn_name])
                    fn = getattr(module, fn_name)
                    return fn(request, experiment_id=experiment_id)
                except (ImportError, AttributeError) as e:
                    logger.error('custom view import failed. view name: %s, '
                                 'error-msg: %s' % (repr(view_fn), e))
                    if settings.DEBUG:
                        raise e

    c['experiment'] = experiment
    c['has_write_permissions'] = \
        authz.has_write_permissions(request, experiment_id)
    c['has_download_permissions'] = \
        authz.has_experiment_download_access(request, experiment_id)
    if request.user.is_authenticated():
        c['is_owner'] = authz.has_experiment_ownership(request, experiment_id)
        c['has_read_or_owner_ACL'] = authz.has_read_or_owner_ACL(request,
                                                                 experiment_id)

    # Enables UI elements for the publication form
    c['pub_form_enabled'] = 'tardis.apps.publication_forms' in \
                            settings.INSTALLED_APPS

    # Enables UI elements for the push_to app
    c['push_to_enabled'] = PushToConfig.name in settings.INSTALLED_APPS
    if c['push_to_enabled']:
        push_to_args = {
            'experiment_id': experiment.pk
        }
        c['push_to_url'] = reverse(initiate_push_experiment, kwargs=push_to_args)

    c['subtitle'] = experiment.title
    c['nav'] = [{'name': 'Data', 'link': '/experiment/view/'},
                {'name': experiment.title,
                 'link': experiment.get_absolute_url()}]

    if 'status' in request.POST:
        c['status'] = request.POST['status']
    if 'error' in request.POST:
        c['error'] = request.POST['error']
    if 'query' in request.GET:
        c['search_query'] = SearchQueryString(request.GET['query'])
    if 'search' in request.GET:
        c['search'] = request.GET['search']
    if 'load' in request.GET:
        c['load'] = request.GET['load']

    _add_protocols_and_organizations(request, experiment, c)

    default_apps = [
        {'name': 'Description',
         'viewfn': 'tardis.tardis_portal.views.experiment_description'},
        {'name': 'Metadata',
         'viewfn': 'tardis.tardis_portal.views.retrieve_experiment_metadata'},
        {'name': 'Sharing', 'viewfn': 'tardis.tardis_portal.views.share'},
        {'name': 'Transfer Datasets',
         'viewfn': 'tardis.tardis_portal.views.experiment_dataset_transfer'},
    ]
    appnames = []
    appurls = []

    for app in getattr(settings, 'EXPERIMENT_APPS', default_apps):
        try:
            appnames.append(app['name'])
            if 'viewfn' in app:
                appurls.append(reverse(app['viewfn'], args=[experiment_id]))
            elif 'url' in app:
                appurls.append(app['url'])
        except:
            logger.debug('error when loading default exp apps')

    from tardis.urls import getTardisApps

    for app in getTardisApps():
        try:
            appnames.append(
                sys.modules['%s.%s.settings'
                            % (settings.TARDIS_APP_ROOT, app)].NAME)
            appurls.append(
                reverse('%s.%s.views.index' % (settings.TARDIS_APP_ROOT,
                                               app), args=[experiment_id]))
        except:
            logger.debug("No tab for %s" % app)

    c['apps'] = zip(appurls, appnames)
    return HttpResponse(render_response_index(request, template_name, c))


@authz.dataset_access_required  # too complex # noqa
def view_dataset(request, dataset_id):
    """Displays a Dataset and associated information.

    Shows a dataset its metadata and a list of associated files with
    the option to show metadata of each file and ways to download those files.
    With write permission this page also allows uploading and metadata
    editing.
    Optionally, if set up in settings.py, datasets of a certain type can
    override the default view.
    Settings example:
    DATASET_VIEWS = [("http://dataset.example/schema",
                      "tardis.apps.custom_views_app.views.my_view_dataset"),]
    """
    dataset = Dataset.objects.get(id=dataset_id)

    if hasattr(settings, "DATASET_VIEWS"):
        namespaces = [ps.schema.namespace
                      for ps in dataset.getParameterSets()]
        for ns, view_fn in settings.DATASET_VIEWS:
            if ns in namespaces:
                x = view_fn.split(".")
                mod_name, fn_name = (".".join(x[:-1]), x[-1])
                try:
                    module = __import__(mod_name, fromlist=[fn_name])
                    fn = getattr(module, fn_name)
                    return fn(request, dataset_id=dataset_id)
                except (ImportError, AttributeError) as e:
                    logger.error('custom view import failed. view name: %s, '
                                 'error-msg: %s' % (repr(view_fn), e))
                    if settings.DEBUG:
                        raise e

    def get_datafiles_page():
        # pagination was removed by someone in the interface but not here.
        # need to fix.
        pgresults = 100

        paginator = Paginator(dataset.datafile_set.all(), pgresults)

        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        # If page request (9999) is out of range, deliver last page of results.

        try:
            return paginator.page(page)
        except (EmptyPage, InvalidPage):
            return paginator.page(paginator.num_pages)

    upload_method = getattr(settings, "UPLOAD_METHOD", False)

    c = {
        'dataset': dataset,
        'datafiles': get_datafiles_page(),
        'parametersets': dataset.getParameterSets()
                                .exclude(schema__hidden=True),
        'has_download_permissions':
        authz.has_dataset_download_access(request, dataset_id),
        'has_write_permissions':
        authz.has_dataset_write(request, dataset_id),
        'from_experiment':
        get_experiment_referer(request, dataset_id),
        'other_experiments':
        authz.get_accessible_experiments_for_dataset(request, dataset_id),
        'upload_method': upload_method
    }

    # Enables UI elements for the push_to app
    c['push_to_enabled'] = PushToConfig.name in settings.INSTALLED_APPS
    if c['push_to_enabled']:
        push_to_args = {
            'dataset_id': dataset.pk
        }
        c['push_to_url'] = reverse(initiate_push_dataset, kwargs=push_to_args)

    _add_protocols_and_organizations(request, dataset, c)
    return HttpResponse(render_response_index(
        request, 'tardis_portal/view_dataset.html', c))


@cache_page(60 * 30)
def stats(request):
    # using count() is more efficient than using len() on a query set
    cursor = connection.cursor()
    if cursor.db.vendor == 'postgresql':
        cursor.execute("SELECT SUM(size::bigint) FROM tardis_portal_datafile")
        try:
            datafile_size = int(cursor.fetchone()[0])
        except TypeError:
            datafile_size = 0
    else:
        datafile_size = DataFile.sum_sizes(DataFile.objects.all())
    c = {
        'experiment_count': Experiment.objects.all().count(),
        'dataset_count': Dataset.objects.all().count(),
        'datafile_count': DataFile.objects.all().count(),
        'datafile_size': datafile_size,
    }
    return HttpResponse(render_response_index(request,
                        'tardis_portal/stats.html', c))


def user_guide(request):
    c = {
        'user_guide_location': getattr(
            settings, 'CUSTOM_USER_GUIDE', 'user_guide/index.html'),
    }
    return HttpResponse(render_response_index(request,
                        'tardis_portal/user_guide.html', c))


@login_required
def sftp_access(request):
    """
    Show dynamically generated instructions on how to connect to SFTP
    :param request: HttpRequest
    :return: HttpResponse
    """
    object_type = request.GET.get('object_type')
    object_id = request.GET.get('object_id')
    sftp_start_dir = ''
    if object_type and object_id:
        ct = ContentType.objects.get_by_natural_key(
            'tardis_portal', object_type)
        item = ct.model_class().objects.get(id=object_id)
        if object_type == 'experiment':
            exps = [item]
            dataset = None
            datafile = None
        else:
            if object_type == 'dataset':
                dataset = item
                datafile = None
            elif object_type == 'datafile':
                datafile = item
                dataset = datafile.dataset
            exps = dataset.experiments.all()
        allowed_exps = []
        for exp in exps:
            if has_experiment_download_access(request, exp.id):
                allowed_exps.append(exp)
        if len(allowed_exps) > 0:
            exp = allowed_exps[0]
            path_parts = ['/home', request.user.username, 'experiments',
                          dirname_with_id(exp.title, exp.id)]
            if dataset is not None:
                path_parts.append(
                    dirname_with_id(dataset.description, dataset.id))
            if datafile is not None:
                path_parts.append(datafile.directory)
            sftp_start_dir = path.join(*path_parts)

    if request.user.userprofile.isDjangoAccount:
        sftp_username = request.user.username
    else:
        login_attr = getattr(settings, 'SFTP_USERNAME_ATTRIBUTE', 'email')
        sftp_username = getattr(request.user, login_attr)
    c = {
        'sftp_host': request.get_host().split(':')[0],
        'sftp_port': getattr(settings, 'SFTP_PORT', 2200),
        'sftp_username': sftp_username,
        'sftp_start_dir': sftp_start_dir,
        'site_name': getattr(settings, 'SITE_TITLE', 'MyTardis'),
    }
    c['sftp_url'] = 'sftp://{}@{}:{}{}'.format(
        c['sftp_username'],
        c['sftp_host'],
        c['sftp_port'],
        c['sftp_start_dir'])
    return render(request, template_name='tardis_portal/sftp.html', context=c)


@login_required
def facility_overview(request):
    '''
    summary of experiments in a facility
    '''
    return HttpResponse(render_response_index(
        request, 'tardis_portal/facility_overview.html'))


def public_data(request):
    '''
    list of public experiments
    '''
    c = {'public_experiments':
         Experiment.safe.public().order_by('-update_time'), }
    return HttpResponse(render_response_index(
        request, 'tardis_portal/public_data.html', c))


def experiment_index(request):
    if request.user.is_authenticated():
        return redirect('tardis_portal.experiment_list_mine')
    else:
        return redirect('tardis_portal.experiment_list_public')


@login_required
def experiment_list_mine(request):

    c = {
        'subtitle': 'My Experiments',
        'can_see_private': True,
        'experiments': authz.get_owned_experiments(request)
                            .order_by('-update_time'),
    }

    # TODO actually change loaders to load this based on stuff
    return HttpResponse(render_response_search(request,
                        'tardis_portal/experiment/list_mine.html', c))


@login_required
def experiment_list_shared(request):

    c = {
        'subtitle': 'Shared Experiments',
        'can_see_private': True,
        'experiments': authz.get_shared_experiments(request)
                            .order_by('-update_time'),
    }

    # TODO actually change loaders to load this based on stuff
    return HttpResponse(render_response_search(request,
                        'tardis_portal/experiment/list_shared.html', c))


def experiment_list_public(request):

    private_filter = Q(public_access=Experiment.PUBLIC_ACCESS_NONE)

    c = {
        'subtitle': 'Public Experiments',
        'can_see_private': False,
        'experiments': Experiment.objects.exclude(private_filter)
                                         .order_by('-update_time'),
    }

    return HttpResponse(render_response_search(request,
                        'tardis_portal/experiment/list_public.html', c))


@permission_required('tardis_portal.add_experiment')
@login_required
def create_experiment(request,
                      template_name='tardis_portal/create_experiment.html'):

    """Create a new experiment view.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param template_name: the path of the template to render
    :type template_name: string
    :rtype: :class:`django.http.HttpResponse`

    """

    c = {
        'subtitle': 'Create Experiment',
        'user_id': request.user.id,
    }

    if request.method == 'POST':
        form = ExperimentForm(request.POST)
        if form.is_valid():
            full_experiment = form.save(commit=False)

            # group/owner assignment stuff, soon to be replaced

            experiment = full_experiment['experiment']
            experiment.created_by = request.user
            full_experiment.save_m2m()

            # add defaul ACL
            acl = ObjectACL(content_object=experiment,
                            pluginId=django_user,
                            entityId=str(request.user.id),
                            canRead=True,
                            canWrite=True,
                            canDelete=True,
                            isOwner=True,
                            aclOwnershipType=ObjectACL.OWNER_OWNED)
            acl.save()

            request.POST = {'status': "Experiment Created."}
            return HttpResponseSeeAlso(reverse(
                'tardis.tardis_portal.views.view_experiment',
                args=[str(experiment.id)]) + "#created")

        c['status'] = "Errors exist in form."
        c["error"] = 'true'
    else:
        form = ExperimentForm(extra=1)

    c['form'] = form
    c['default_institution'] = settings.DEFAULT_INSTITUTION
    return HttpResponse(render_response_index(request, template_name, c))


@login_required
@permission_required('tardis_portal.change_experiment')
@authz.write_permissions_required
def edit_experiment(request, experiment_id,
                    template="tardis_portal/create_experiment.html"):
    """Edit an existing experiment.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param experiment_id: the ID of the experiment to be edited
    :type experiment_id: string
    :param template_name: the path of the template to render
    :type template_name: string
    :rtype: :class:`django.http.HttpResponse`

    """
    experiment = Experiment.objects.get(id=experiment_id)

    c = {'subtitle': 'Edit Experiment',
         'experiment_id': experiment_id, }

    if request.method == 'POST':
        form = ExperimentForm(data=request.POST, instance=experiment, extra=0)
        if form.is_valid():
            full_experiment = form.save(commit=False)
            experiment = full_experiment['experiment']
            experiment.created_by = request.user
            full_experiment.save_m2m()

            request.POST = {'status': "Experiment Saved."}
            return HttpResponseSeeAlso(reverse(
                'tardis.tardis_portal.views.view_experiment',
                args=[str(experiment.id)]) + "#saved")

        c['status'] = "Errors exist in form."
        c["error"] = 'true'
    else:
        form = ExperimentForm(instance=experiment, extra=0)

    c['form'] = form

    return HttpResponse(render_response_index(request, template, c))


@login_required
def add_dataset(request, experiment_id):
    if not has_experiment_write(request, experiment_id):
        return HttpResponseForbidden()

    # Process form or prepopulate it
    if request.method == 'POST':
        form = DatasetForm(request.POST)
        if form.is_valid():
            dataset = Dataset()
            dataset.description = form.cleaned_data['description']
            dataset.save()
            experiment = Experiment.objects.get(id=experiment_id)
            dataset.experiments.add(experiment)
            dataset.save()
            return _redirect_303('tardis.tardis_portal.views.view_dataset',
                                 dataset.id)
    else:
        form = DatasetForm()

    c = {'form': form}
    return HttpResponse(render_response_index(request,
                        'tardis_portal/add_or_edit_dataset.html', c))


@login_required
def edit_dataset(request, dataset_id):
    if not has_dataset_write(request, dataset_id):
        return HttpResponseForbidden()
    dataset = Dataset.objects.get(id=dataset_id)

    # Process form or prepopulate it
    if request.method == 'POST':
        form = DatasetForm(request.POST)
        if form.is_valid():
            dataset.description = form.cleaned_data['description']
            dataset.save()
            return _redirect_303('tardis.tardis_portal.views.view_dataset',
                                 dataset.id)
    else:
        form = DatasetForm(instance=dataset)

    c = {'form': form, 'dataset': dataset}
    return HttpResponse(render_response_index(request,
                        'tardis_portal/add_or_edit_dataset.html', c))


@login_required()
def control_panel(request):

    experiments = Experiment.safe.owned(request.user)
    if experiments:
        experiments = experiments.order_by('title')

    c = {'experiments': experiments,
         'subtitle': 'Experiment Control Panel'}

    return HttpResponse(render_response_index(request,
                        'tardis_portal/control_panel.html', c))
