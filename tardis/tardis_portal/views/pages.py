"""
views that render full pages
"""

import logging
import re
from os import path
import inspect
import types

from six import string_types

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.urls import reverse
from django.db import connection
from django.db.models import Q
from django.http import (HttpResponse,
                         HttpResponseForbidden,
                         JsonResponse)
from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_page
from django.views.generic.base import TemplateView, View

from tardis.search.utils import SearchQueryString
from ..auth import decorators as authz
from ..auth.decorators import (
    has_experiment_download_access, has_experiment_write, has_dataset_write)
from ..auth.localdb_auth import django_user
from ..forms import ExperimentForm, DatasetForm
from ..models import Experiment, Dataset, DataFile, ObjectACL
from ..shortcuts import render_response_index, \
    return_response_error, return_response_not_found, get_experiment_referer, \
    render_response_search
from ..views.utils import (
    _redirect_303, _add_protocols_and_organizations, HttpResponseSeeAlso)
from ..util import get_filesystem_safe_dataset_name

logger = logging.getLogger(__name__)


def site_routed_view(request, _default_view, _site_mappings, *args, **kwargs):
    """
    Allows a view to be overriden based on the Site (eg domain) for the current
    request. Takes a default fallback view (_default_view) and a dictionary
    mapping Django Sites (domain name or int SITE_ID) to views. If the current
    request matches a Site in the dictionary, that view is used instead of the
    default.

    The intention is to define {site: view} mappings in settings.py, and use
    this wrapper view in urls.py to allow a single URL to be routed to
    different views depending on the Site in the request.

    :param request: a HTTP request object
    :type request: :class:`django.http.HttpRequest`
    :param _default_view: The default view if no Site in _site_mappings matches
                          the current Site.
    :type _default_view: types.FunctionType | str
    :param _site_mappings: A dictionary mapping Django sites to views
                          (sites are specified as either a domain name str or
                           int SITE_ID).
    :type _site_mappings: dict
    :param args:
    :type args:
    :param kwargs:
    :type kwargs:
    :return: A view function
    :rtype: types.FunctionType
    """
    view = None
    if _site_mappings:
        site = get_current_site(request)
        # try to find an overriding view based on domain name or SITE_ID
        # (int)
        view = _site_mappings.get(site.domain, None) or \
            _site_mappings.get(site.id, None)
    if view:
        try:
            view_fn = _resolve_view(view)
            return view_fn(request, *args, **kwargs)
        except (ImportError, AttributeError) as e:
            logger.error('custom view import failed. using default index'
                         'view as fallback. view name: %s, error-msg: %s'
                         % (repr(view), e))
            if settings.DEBUG:
                raise e
    view_fn = _resolve_view(_default_view)
    return view_fn(request, *args, **kwargs)


def use_rapid_connect(fn):
    """
    A decorator that adds AAF Rapid Connect settings to a get_context_data
    method.

    :param fn: A get_context_data function/method.
    :type fn: types.FunctionType
    :return: A get_context_data function that adds RAPID_CONNECT_* keys to its
             output context.
    :rtype: types.FunctionType
    """

    def add_rapid_connect_settings(cxt, *args, **kwargs):
        c = fn(cxt, *args, **kwargs)

        c['RAPID_CONNECT_ENABLED'] = getattr(settings,
                                             'RAPID_CONNECT_ENABLED', False)

        if c['RAPID_CONNECT_ENABLED']:
            c['RAPID_CONNECT_LOGIN_URL'] = \
                getattr(settings, 'RAPID_CONNECT_CONFIG', {}).get(
                    'authnrequest_url',
                    None)

            if not c['RAPID_CONNECT_LOGIN_URL']:
                raise ImproperlyConfigured(
                    "RAPID_CONNECT_CONFIG['authnrequest_url'] must be "
                    "configured in settings if RAPID_CONNECT_ENABLED is True.")
        return c

    return add_rapid_connect_settings


class IndexView(TemplateView):
    template_name = 'tardis_portal/index.html'

    @use_rapid_connect
    def get_context_data(self, request, **kwargs):
        """
        Prepares the values to be passed to the default index view - a list of
        experiments, respecting authorization rules.

        :param request: a HTTP request object
        :type request: :class:`django.http.HttpRequest`
        :param dict kwargs: kwargs
        :return: A dictionary of values for the view/template.
        :rtype: dict
        """
        c = super(IndexView, self).get_context_data(**kwargs)
        status = ''
        limit = 8
        c['status'] = status
        if request.user.is_authenticated:
            private_experiments = Experiment.safe.owned_and_shared(
                    request.user).order_by('-update_time')[:limit]
            c['private_experiments'] = private_experiments
            if len(private_experiments) > 4:
                limit = 4
        public_experiments = Experiment.objects.exclude(
                public_access=Experiment.PUBLIC_ACCESS_NONE).exclude(
                public_access=Experiment.PUBLIC_ACCESS_EMBARGO).order_by(
                '-update_time')[:limit]
        c['public_experiments'] = public_experiments

        return c

    def get(self, request, *args, **kwargs):
        """
        The index view, intended to render the front page of the MyTardis site
        listing recent experiments.

        This default view can be overriden by defining a dictionary INDEX_VIEWS
        in settings which maps SITE_ID's or domain names to an alternative view
        function (similar to the DATASET_VIEWS or EXPERIMENT_VIEWS overrides).

        :param request: a HTTP request object
        :type request: :class:`django.http.HttpRequest`
        :param list args:
        :param dict kwargs:
        :return: The Django response object
        :rtype: :class:`django.http.HttpResponse`
        """

        c = self.get_context_data(request, **kwargs)

        return render_response_index(request, self.template_name, c)


class DatasetView(TemplateView):
    template_name = 'tardis_portal/view_dataset.html'

    # TODO: Can me make this a generic function like site_routed_view
    #       that will take an Experiment, Dataset or DataFile and
    #       the associated routing list from settings ?
    # eg
    # schema_routed_view(request, model_instance,
    #                    view_override_tuples, **kwargs)
    def find_custom_view_override(self, request, dataset):
        """
        Determines if any custom view overrides have been defined in
        settings.DATASET_VIEWS and returns the view function if a match
        to one the schemas for the dataset is found.
        (DATASET_VIEWS is a list of (schema_namespace, view_function) tuples).

        :param request:
        :type request:
        :param dataset:
        :type dataset:
        :return:
        :rtype:
        """
        if hasattr(settings, "DATASET_VIEWS"):
            namespaces = [ps.schema.namespace
                          for ps in dataset.getParameterSets()]
            for ns, view_fn in settings.DATASET_VIEWS:
                ns_match = next((n for n in namespaces if re.match(ns, n)),
                                None)
                if ns_match:
                    try:
                        fn = _resolve_view(view_fn)
                        return fn(request, dataset_id=dataset.id)
                    except (ImportError, AttributeError) as e:
                        logger.error(
                            'custom view import failed. view name: %s, '
                            'error-msg: %s' % (repr(view_fn), e))
                        if settings.DEBUG:
                            raise e
        return None

    def get_context_data(self, request, dataset, **kwargs):
        """
        Prepares the values to be passed to the default dataset view,
        respecting authorization rules. Returns a dict of values (the context).

        :param request: a HTTP request object
        :type request: :class:`django.http.HttpRequest`
        :param dataset: the Dataset model instance
        :type dataset: tardis.tardis_portal.models.dataset.Dataset
        :param dict kwargs:
        :return: A dictionary of values for the view/template.
        :rtype: dict
        """

        def get_datafiles_page():
            # pagination was removed by someone in the interface but not here.
            # need to fix.
            pgresults = 100

            paginator = Paginator(dataset.datafile_set.all(), pgresults)

            try:
                page = int(request.GET.get('page', '1'))
            except ValueError:
                page = 1

            # If page request is out of range (eg 9999), deliver last page of
            # results.
            try:
                return paginator.page(page)
            except (EmptyPage, InvalidPage):
                return paginator.page(paginator.num_pages)

        c = super(DatasetView, self).get_context_data(**kwargs)

        dataset_id = dataset.id
        dataset_instrument = dataset.instrument
        if dataset_instrument:
            instrument_name = dataset_instrument.name
            dataset_facility = dataset_instrument.facility
            facility_name = dataset_facility.name if dataset_facility else None
        else:
            instrument_name = None
            facility_name = None
        upload_method = getattr(settings, "UPLOAD_METHOD", False)
        max_images_in_carousel = getattr(settings, "MAX_IMAGES_IN_CAROUSEL", 0)
        if max_images_in_carousel:
            carousel_slice = ":%s" % max_images_in_carousel
        else:
            carousel_slice = ":"

        c.update(
            {'dataset': dataset,
             'datafiles': get_datafiles_page(),
             'parametersets': dataset.getParameterSets().exclude(
                     schema__hidden=True),
             'has_download_permissions': authz.has_dataset_download_access(
                 request, dataset_id),
             'has_write_permissions': authz.has_dataset_write(request,
                                                              dataset_id),
             'from_instrument': instrument_name,
             'from_facility': facility_name,
             'from_experiment': get_experiment_referer(request, dataset_id),
             'other_experiments': authz.get_accessible_experiments_for_dataset(
                 request,
                 dataset_id),
             'upload_method': upload_method,
             'push_to_enabled': 'tardis.apps.push_to' in settings.INSTALLED_APPS,
             'carousel_slice': carousel_slice,
             }
        )

        # Enables UI elements for the push_to app
        if c['push_to_enabled']:
            push_to_args = {
                'dataset_id': dataset.pk
            }
            c['push_to_url'] = reverse('tardis.apps.push_to.views.initiate_push_dataset',
                                       kwargs=push_to_args)

        _add_protocols_and_organizations(request, dataset, c)

        return c

    def get(self, request, *args, **kwargs):
        """
        View an existing dataset.

        This default view can be overriden by defining a dictionary
        DATASET_VIEWS in settings.

        :param request: a HTTP request object
        :type request: :class:`django.http.HttpRequest`
        :param list args:
        :param dict kwargs:
        :return: The Django response object
        :rtype: :class:`django.http.HttpResponse`
        """
        if not request.user.is_authenticated:
            return return_response_error(request)

        dataset_id = kwargs.get('dataset_id', None)
        if dataset_id is None:
            return return_response_error(request)

        try:
            dataset = Dataset.objects.get(id=dataset_id)
        except PermissionDenied:
            return return_response_error(request)
        except Dataset.DoesNotExist:
            return return_response_not_found(request)

        view_override = self.find_custom_view_override(request, dataset)
        if view_override is not None:
            return view_override

        c = self.get_context_data(request, dataset, **kwargs)

        template_name = kwargs.get('template_name', None)
        if template_name is None:
            template_name = self.template_name

        return render_response_index(request, template_name, c)


def about(request):

    c = {'subtitle': 'About',
         'about_pressed': True,
         'nav': [{'name': 'About', 'link': '/about/'}],
         'custom_about_section': getattr(
             settings, 'CUSTOM_ABOUT_SECTION_TEMPLATE',
             'tardis_portal/about_include.html'),
         }
    return render_response_index(request, 'tardis_portal/about.html', c)


@login_required
def my_data(request):
    '''
    show data with credential-based access
    delegate to custom views depending on settings
    '''

    owned_experiments = \
        Experiment.safe.owned(request.user).order_by('-update_time')
    shared_experiments = \
        Experiment.safe.shared(request.user).order_by('-update_time')

    c = {
        'owned_experiments': owned_experiments,
        'shared_experiments': shared_experiments
    }
    return render_response_index(request, 'tardis_portal/my_data.html', c)


def _resolve_view(view_function_or_string):
    """
    Takes a string representing a 'module.app.view' function, a view function
    itself, or View class. Imports the module and returns the view function, eg
    'tardis.apps.my_custom_app.views.my_special_view' will
    return the my_special_view function defined in views.py in
    that app.
    Auto detects class-based views.

    Will raise ImportError or AttributeError if the module or
    view function don't exist, respectively.

    :param view_function_or_string: A string representing the view,
                                    or a function itself
    :type view_function_or_string: basestring | types.FunctionType
    :return: The view function
    :rtype: types.FunctionType
    :raises TypeError:
    """
    if isinstance(view_function_or_string, string_types):
        x = view_function_or_string.split('.')
        obj_path, obj_name = ('.'.join(x[:-1]), x[-1])
        module = __import__(obj_path, fromlist=[obj_name])
        obj = getattr(module, obj_name)
    elif isinstance(view_function_or_string, types.FunctionType):
        obj = view_function_or_string
    else:
        raise TypeError("Must provide a string or a view function")

    if inspect.isclass(obj) and issubclass(obj, View):
        obj = obj.as_view()

    return obj


class ExperimentView(TemplateView):
    template_name = 'tardis_portal/view_experiment.html'

    # TODO: Can me make this a generic function like site_routed_view
    #       that will take an Experiment, Dataset or DataFile and
    #       the associated routing list from settings ?
    # eg
    # schema_routed_view(request, model_instance,
    #                    view_override_tuples, **kwargs)
    def find_custom_view_override(self, request, experiment):
        if hasattr(settings, "EXPERIMENT_VIEWS"):
            namespaces = [ps.schema.namespace
                          for ps in experiment.getParameterSets()]
            for ns, view_fn in settings.EXPERIMENT_VIEWS:
                ns_match = next((n for n in namespaces if re.match(ns, n)),
                                None)
                if ns_match:
                    try:
                        fn = _resolve_view(view_fn)
                        return fn(request, experiment_id=experiment.id)
                    except (ImportError, AttributeError) as e:
                        logger.error(
                            'custom view import failed. view name: %s, '
                            'error-msg: %s' % (repr(view_fn), e))
                        if settings.DEBUG:
                            raise e
        return None

    def get_context_data(self, request, experiment, **kwargs):
        """
        Prepares the values to be passed to the default experiment view,
        respecting authorization rules. Returns a dict of values (the context).

        :param request: a HTTP request object
        :type request: :class:`django.http.HttpRequest`
        :param experiment: the experiment model instance
        :type experiment: tardis.tardis_portal.models.experiment.Experiment
        :param dict kwargs: kwargs
        :return: A dictionary of values for the view/template.
        :rtype: dict
        """

        c = super(ExperimentView, self).get_context_data(**kwargs)

        c['experiment'] = experiment
        c['has_write_permissions'] = \
            authz.has_write_permissions(request, experiment.id)
        c['has_download_permissions'] = \
            authz.has_experiment_download_access(request, experiment.id)
        if request.user.is_authenticated:
            c['is_owner'] = \
                authz.has_experiment_ownership(request, experiment.id)
            c['has_read_or_owner_ACL'] = \
                authz.has_read_or_owner_ACL(request, experiment.id)

        # Enables UI elements for the push_to app
        c['push_to_enabled'] = 'tardis.apps.push_to' in settings.INSTALLED_APPS
        if c['push_to_enabled']:
            push_to_args = {
                'experiment_id': experiment.pk
            }
            c['push_to_url'] = reverse('tardis.apps.push_to.views.initiate_push_experiment',
                                       kwargs=push_to_args)

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
             'viewfn':
             'tardis.tardis_portal.views.retrieve_experiment_metadata'},
            {'name': 'Sharing', 'viewfn': 'tardis.tardis_portal.views.share'},
            {'name': 'Transfer Datasets',
             'viewfn':
             'tardis.tardis_portal.views.experiment_dataset_transfer'},
        ]
        appnames = []
        appurls = []

        for app in getattr(settings, 'EXPERIMENT_APPS', default_apps):
            try:
                appnames.append(app['name'])
                if 'viewfn' in app:
                    appurls.append(reverse(app['viewfn'],
                                   args=[experiment.id]))
                elif 'url' in app:
                    appurls.append(app['url'])
            except:
                logger.debug('error when loading default exp apps')

        c['apps'] = zip(appurls, appnames)

        return c

    def get(self, request, *args, **kwargs):
        """
        View an existing experiment.

        This default view can be overriden by defining a dictionary
        EXPERIMENT_VIEWS in settings.

        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`
        :param list args:
        :param dict kwargs:
        in kwargs: param int experiment_id: the ID of the experiment
        :returns: an HttpResponse
        :rtype: :class:`django.http.HttpResponse`
        """
        if not request.user.is_authenticated:
            return return_response_error(request)

        experiment_id = kwargs.get('experiment_id', None)
        if experiment_id is None:
            return return_response_error(request)

        try:
            experiment = Experiment.safe.get(request.user, experiment_id)
        except PermissionDenied:
            return return_response_error(request)
        except Experiment.DoesNotExist:
            return return_response_not_found(request)

        if not experiment:
            return return_response_not_found(request)

        view_override = self.find_custom_view_override(request, experiment)
        if view_override is not None:
            return view_override

        c = self.get_context_data(request, experiment)

        template_name = kwargs.get('template_name', None)
        if template_name is None:
            template_name = self.template_name

        return render_response_index(request, template_name, c)


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
    return render_response_index(request, 'tardis_portal/stats.html', c)


def user_guide(request):
    c = {
        'user_guide_location': getattr(
            settings, 'CUSTOM_USER_GUIDE', 'user_guide/index.html'),
    }
    return render_response_index(request, 'tardis_portal/user_guide.html', c)


@login_required
def sftp_access(request):
    """
    Show dynamically generated instructions on how to connect to SFTP
    :param Request request: HttpRequest
    :return: HttpResponse
    :rtype: HttpResponse
    """
    from ..download import make_mapper
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
        if allowed_exps:
            path_mapper = make_mapper(settings.DEFAULT_PATH_MAPPER,
                                      rootdir=None)
            exp = allowed_exps[0]
            path_parts = ['/home', request.user.username, 'experiments',
                          path_mapper(exp)]
            if dataset is not None:
                path_parts.append(path_mapper(dataset))
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
    return render_response_index(
        request, 'tardis_portal/facility_overview.html')


def public_data(request):
    '''
    list of public experiments
    '''
    c = {'public_experiments':
         Experiment.safe.public().order_by('-update_time'), }
    return render_response_index(request, 'tardis_portal/public_data.html', c)


def experiment_index(request):
    if request.user.is_authenticated:
        return redirect('tardis.tardis_portal.views.experiment_list_mine')
    return redirect('tardis.tardis_portal.views.experiment_list_public')


@login_required
def experiment_list_mine(request):

    c = {
        'subtitle': 'My Experiments',
        'can_see_private': True,
        'experiments': authz.get_owned_experiments(request)
                            .order_by('-update_time'),
    }

    # TODO actually change loaders to load this based on stuff
    return render_response_search(
        request, 'tardis_portal/experiment/list_mine.html', c)


@login_required
def experiment_list_shared(request):

    c = {
        'subtitle': 'Shared Experiments',
        'can_see_private': True,
        'experiments': authz.get_shared_experiments(request)
                            .order_by('-update_time'),
    }

    # TODO actually change loaders to load this based on stuff
    return render_response_search(
        request, 'tardis_portal/experiment/list_shared.html', c)


def experiment_list_public(request):

    private_filter = Q(public_access=Experiment.PUBLIC_ACCESS_NONE)

    c = {
        'subtitle': 'Public Experiments',
        'can_see_private': False,
        'experiments': Experiment.objects.exclude(private_filter)
                                         .order_by('-update_time'),
    }

    return render_response_search(
        request, 'tardis_portal/experiment/list_public.html', c)


@permission_required('tardis_portal.add_experiment')
@login_required
def create_experiment(request,
                      template_name='tardis_portal/create_experiment.html'):

    """Create a new experiment view.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param template_name: the path of the template to render
    :type template_name: string
    :returns: an HttpResponse
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
            return HttpResponseSeeAlso(reverse('tardis_portal.view_experiment',
                                       args=[str(experiment.id)]) + "#created")

        c['status'] = "Errors exist in form."
        c["error"] = 'true'
    else:
        form = ExperimentForm(extra=1)

    c['form'] = form
    c['default_institution'] = settings.DEFAULT_INSTITUTION
    return render_response_index(request, template_name, c)


@login_required
@permission_required('tardis_portal.change_experiment')
@authz.write_permissions_required
def edit_experiment(request, experiment_id,
                    template="tardis_portal/create_experiment.html"):
    """Edit an existing experiment.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param experiment_id: the ID of the experiment to be edited
    :type experiment_id: str | int
    :param template: the path of the template to render
    :type template: str | int
    :returns: an HttpResponse
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
            return HttpResponseSeeAlso(reverse('tardis_portal.view_experiment',
                                               args=[str(experiment.id)]) +
                                       "#saved")

        c['status'] = "Errors exist in form."
        c["error"] = 'true'
    else:
        form = ExperimentForm(instance=experiment, extra=0)

    c['form'] = form

    return render_response_index(request, template, c)


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
            dataset.instrument = form.cleaned_data['instrument']
            dataset.directory = form.cleaned_data['directory']
            dataset.save()
            experiment = Experiment.objects.get(id=experiment_id)
            dataset.experiments.add(experiment)
            dataset.save()
            return _redirect_303('tardis_portal.view_dataset',
                                 dataset.id)
    else:
        form = DatasetForm()

    c = {'form': form}
    return render_response_index(
        request, 'tardis_portal/add_or_edit_dataset.html', c)


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
            dataset.instrument = form.cleaned_data['instrument']
            dataset.directory = form.cleaned_data['directory']
            dataset.save()
            return _redirect_303('tardis_portal.view_dataset',
                                 dataset.id)
    else:
        form = DatasetForm(instance=dataset)

    c = {'form': form, 'dataset': dataset}
    return render_response_index(
        request, 'tardis_portal/add_or_edit_dataset.html', c)


@login_required()
def control_panel(request):

    experiments = Experiment.safe.owned(request.user)
    if experiments:
        experiments = experiments.order_by('title')

    c = {'experiments': experiments,
         'subtitle': 'Experiment Control Panel'}

    return render_response_index(
        request, 'tardis_portal/control_panel.html', c)


def _get_dataset_checksums(dataset, type='md5'):
    valid_types = ['md5', 'sha512']
    if type not in valid_types:
        raise ValueError('Invalid checksum type (%s). Valid values are %s' %
                         (type, ', '.join(valid_types)))
    hash_attr = type+'sum'
    checksums = [(getattr(df, hash_attr), path.join(df.directory or '', df.filename))
                 for df in dataset.get_datafiles()]
    return checksums


@authz.dataset_access_required  # too complex # noqa
def checksums_download(request, dataset_id, **kwargs):
    dataset = Dataset.objects.get(id=dataset_id)
    if not dataset:
        return return_response_not_found(request)

    type = request.GET.get('type', 'md5')
    format = request.GET.get('format', 'text')

    checksums = _get_dataset_checksums(dataset, type)
    if format == 'text':
        checksum_doc = ''.join(["%s  %s\n" % c for c in checksums])
        checksum_doc += '\n'
        response = HttpResponse(checksum_doc, content_type='text/plain')
        response['Content-Disposition'] = \
            '%s; filename="%s-manifest-md5.txt"' % (
            'attachment',
            get_filesystem_safe_dataset_name(dataset))
        return response

    elif format == 'json':
        jdict = {'checksums': []}
        for c in checksums:
            jdict['checksums'].append({'checksum': c[0], 'file': c[1], 'type': type})

        return JsonResponse(jdict)
    else:
        raise ValueError("Invalid format. Valid formats are 'text' or 'json'")
