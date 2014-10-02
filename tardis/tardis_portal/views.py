# -*- coding: utf-8 -*- # pylint: disable=C0302
#
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2011, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
views.py

.. moduleauthor:: Steve Androulakis <steve.androulakis@monash.edu>
.. moduleauthor:: Gerson Galang <gerson.galang@versi.edu.au>
.. moduleauthor:: Ulrich Felzmaann <ulrich.felzmann@versi.edu.au>

"""
import time

from tardis.tardis_portal.auth.decorators import \
    has_experiment_write, has_dataset_write

from base64 import b64decode
import urllib2
from urllib import urlencode
from urlparse import urlparse, parse_qs

from os import path
import logging
import json
from operator import itemgetter

from django.template import Context
from django.conf import settings
from django.db import connection
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render_to_response, redirect, render
from django.contrib.auth.models import User, Group
from django.http import HttpResponseRedirect, HttpResponse,\
    HttpResponseForbidden, HttpResponseNotFound
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.exceptions import PermissionDenied
from django.forms.models import model_to_dict
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.contrib.sites.models import Site
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat

from tardis.urls import getTardisApps
from tardis.tardis_portal.forms import ExperimentForm, DatasetForm, \
    createSearchDatafileForm, createSearchDatafileSelectionForm, \
    LoginForm, createSearchExperimentForm, \
    ChangeGroupPermissionsForm, ChangeUserPermissionsForm, \
    create_parameterset_edit_form, \
    save_datafile_edit_form, create_datafile_add_form,\
    save_datafile_add_form, MXDatafileSearchForm, RightsForm,\
    ManageAccountForm, CreateGroupPermissionsForm,\
    CreateUserPermissionsForm

from tardis.tardis_portal.errors import UnsupportedSearchQueryTypeError

from tardis.tardis_portal.staging import get_full_staging_path, \
    staging_list

from tardis.tardis_portal.tasks import create_staging_datafiles

from tardis.tardis_portal.models import Experiment, ExperimentParameter, \
    DatafileParameter, DatasetParameter, ObjectACL, DataFile, \
    DatafileParameterSet, ParameterName, GroupAdmin, Schema, \
    Dataset, ExperimentParameterSet, DatasetParameterSet, \
    License, UserProfile, UserAuthentication, Token

from tardis.tardis_portal.models.facility import facilities_managed_by

from tardis.tardis_portal import constants
from tardis.tardis_portal.auth.localdb_auth import django_user
from tardis.tardis_portal.auth.localdb_auth import auth_key as localdb_auth_key
from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.auth import auth_service
from tardis.tardis_portal.shortcuts import render_response_index, \
    return_response_error, return_response_not_found, \
    render_response_search, get_experiment_referer
from tardis.tardis_portal.hacks import oracle_dbops_hack
from tardis.tardis_portal.util import generate_file_checksums
from tardis.tardis_portal.util import render_public_access_badge

from haystack.views import SearchView
from haystack.query import SearchQuerySet
from tardis.tardis_portal.search_query import FacetFixedSearchQuery
from tardis.tardis_portal.forms import RawSearchForm
from tardis.tardis_portal.search_backend import HighlightSearchBackend
from django.contrib.auth import logout as django_logout

from django.views.decorators.csrf import csrf_exempt
import django.contrib.auth as djauth
from tardis.tardis_portal.auth import jwt
import pwgen
from tardis.tardis_portal.models.jti import JTI

logger = logging.getLogger(__name__)


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


def _redirect_303(*args, **kwargs):
    response = redirect(*args, **kwargs)
    response.status_code = 303
    return response


def getNewSearchDatafileSelectionForm(initial=None):
    DatafileSelectionForm = createSearchDatafileSelectionForm(initial)
    return DatafileSelectionForm()


def logout(request):
    if 'datafileResults' in request.session:
        del request.session['datafileResults']

    # Remove AAF attributes.
    del request.session['attributes']
    del request.session['jwt']
    del request.session['jws']

    c = Context({})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/index.html', c))


def index(request):
    status = ''
    limit = 8
    c = Context({'status': status})
    if request.user.is_authenticated():
        private_experiments = Experiment.safe.owned_and_shared(request.user)\
            .order_by('-update_time')[:limit]
        c['private_experiments'] = private_experiments
        if len(private_experiments) > 4:
            limit = 4
    public_experiments = Experiment.objects\
        .exclude(public_access=Experiment.PUBLIC_ACCESS_NONE)\
        .order_by('-update_time')[:limit]
    c['public_experiments'] = public_experiments
    return HttpResponse(render_response_index(request,
                        'tardis_portal/index.html', c))


def site_settings(request):

    if request.method == 'POST':
        if 'username' in request.POST and 'password' in request.POST:

            user = auth_service.authenticate(request=request,
                                             authMethod=localdb_auth_key)
            if user is not None:
                if user.is_staff:

                    x509 = open(settings.GRID_PROXY_FILE, 'r')

                    c = Context({
                        'baseurl': request.build_absolute_uri('/'),
                        'proxy': x509.read(), 'filestorepath':
                        settings.FILE_STORE_PATH})
                    return HttpResponse(render_response_index(
                        request,
                        'tardis_portal/site_settings.xml',
                        c), mimetype='application/xml')

    return return_response_error(request)


@never_cache
def load_image(request, parameter):
    file_path = path.abspath(path.join(settings.METADATA_STORE_PATH,
                                       parameter.string_value))

    from django.core.servers.basehttp import FileWrapper
    wrapper = FileWrapper(file(file_path))
    return HttpResponse(wrapper, mimetype=parameter.name.units)


def load_experiment_image(request, parameter_id):
    parameter = ExperimentParameter.objects.get(pk=parameter_id)
    experiment_id = parameter.parameterset.experiment.id
    if authz.has_experiment_access(request, experiment_id):
        return load_image(request, parameter)
    else:
        return return_response_error(request)


def load_dataset_image(request, parameter_id):
    parameter = DatasetParameter.objects.get(pk=parameter_id)
    dataset = parameter.parameterset.dataset
    if authz.has_dataset_access(request, dataset.id):
        return load_image(request, parameter)
    else:
        return return_response_error(request)


def load_datafile_image(request, parameter_id):
    try:
        parameter = DatafileParameter.objects.get(pk=parameter_id)
    except DatafileParameter.DoesNotExist:
        return HttpResponseNotFound()
    datafile = parameter.parameterset.datafile
    if authz.has_datafile_access(request, datafile.id):
        return load_image(request, parameter)
    else:
        return return_response_error(request)


@authz.experiment_access_required
def display_experiment_image(
        request, experiment_id, parameterset_id, parameter_name):

    # TODO handle not exist

    if not authz.has_experiment_access(request, experiment_id):
        return return_response_error(request)

    image = ExperimentParameter.objects.get(name__name=parameter_name,
                                            parameterset=parameterset_id)

    return HttpResponse(b64decode(image.string_value), mimetype='image/jpeg')


@authz.dataset_access_required
def display_dataset_image(
        request, dataset_id, parameterset_id, parameter_name):

    # TODO handle not exist

    if not authz.has_dataset_access(request, dataset_id):
        return return_response_error(request)

    image = DatasetParameter.objects.get(name__name=parameter_name,
                                         parameterset=parameterset_id)

    return HttpResponse(b64decode(image.string_value), mimetype='image/jpeg')


@authz.datafile_access_required
def display_datafile_image(
        request, datafile_id, parameterset_id, parameter_name):

    # TODO handle not exist

    if not authz.has_datafile_access(request, datafile_id):
        return return_response_error(request)

    image = DatafileParameter.objects.get(name__name=parameter_name,
                                          parameterset=parameterset_id)

    return HttpResponse(b64decode(image.string_value), mimetype='image/jpeg')


@authz.dataset_access_required
def dataset_thumbnail(request, dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)
    tn_url = dataset.get_thumbnail_url()
    if tn_url is None:
        return HttpResponseNotFound()
    return HttpResponseRedirect(tn_url)


def about(request):

    c = Context({'subtitle': 'About',
                 'about_pressed': True,
                 'nav': [{'name': 'About', 'link': '/about/'}],
                 'version': settings.MYTARDIS_VERSION,
                 })
    return HttpResponse(render_response_index(request,
                        'tardis_portal/about.html', c))


@login_required
def my_data(request):
    '''
    show data with credential-based access
    delegate to custom views depending on settings
    '''

    c = Context({
        'owned_experiments': Experiment.safe.owned(request.user)
        .order_by('-update_time'),
        'shared_experiments': Experiment.safe.shared(request.user)
        .order_by('-update_time'),
    })
    return HttpResponse(render_response_index(
        request, 'tardis_portal/my_data.html', c))


@login_required
def facility_overview(request):
    '''
    summary of experiments in a facility
    '''
    return HttpResponse(render_response_index(
        request, 'tardis_portal/facility_overview.html'))


@never_cache
@login_required
def fetch_facility_data(request):
    '''
    json facility datasets
    '''
    # In lieu of proper pagination, only the 500 most recent datasets are
    # fetched
    dataset_objects = Dataset.objects.filter(
        instrument__facility__manager_group__user=request.user
    ).order_by('-id')[:500]

    def datetime_to_us(dt):
        '''
        The datetime objects are kept as None if they aren't set, otherwise
        they're converted to milliseconds so AngularJS can format them nicely.
        '''
        if dt is None:
            return None
        return time.mktime(dt.timetuple()) * 1000 + dt.microsecond / 1000

    # Select only the bits we want from the models
    facility_data = []
    for dataset in dataset_objects:
        instrument = dataset.instrument
        facility = instrument.owner_facility
        parent_experiment = dataset.experiments.get()
        datafile_objects = DataFile.objects.filter(dataset=dataset)
        owner = parent_experiment.created_by
        datafiles = []
        dataset_size = 0
        for datafile in datafile_objects:
            datafiles.append({
                "id": datafile.id,
                "filename": datafile.filename,
                "size": int(datafile.size),
                "created_time": datetime_to_us(datafile.created_time),
                "modification_time": datetime_to_us(datafile.modification_time)
            })
            dataset_size = dataset_size + int(datafile.size)
        obj = {
            "id": dataset.id,
            "parent_experiment": {
                "id": parent_experiment.id,
                "title": parent_experiment.title,
                "created_time": datetime_to_us(parent_experiment.created_time),
            },
            "description": dataset.description,
            "institution": parent_experiment.institution_name,
            "datafiles": datafiles,
            "size": dataset_size,
            "owner": {
                "id": owner.id,
                "name": owner.username,
            },
            "instrument": {
                "id": instrument.id,
                "name": instrument.name,
            },
            "facility": {
                "id": facility.id,
                "name": facility.name,
            },
        }
        facility_data.append(obj)

    return HttpResponse(json.dumps(facility_data), mimetype='application/json')


@never_cache
@login_required
def fetch_facilities_list(request):
    '''
    json list of facilities managed by the current user
    '''
    facility_data = []
    for facility in facilities_managed_by(request.user):
        facility_data.append({"id": facility.id, "name": facility.name})

    return HttpResponse(json.dumps(facility_data), mimetype='application/json')


def public_data(request):
    '''
    list of public experiments
    '''
    c = Context({
        'public_experiments': Experiment.safe.public(),
    })
    return HttpResponse(render_response_index(
        request, 'tardis_portal/public_data.html', c))


def experiment_index(request):
    if request.user.is_authenticated():
        return redirect('tardis_portal.experiment_list_mine')
    else:
        return redirect('tardis_portal.experiment_list_public')


@login_required
def experiment_list_mine(request):

    c = Context({
        'subtitle': 'My Experiments',
        'can_see_private': True,
        'experiments': authz.get_owned_experiments(request)
                            .order_by('-update_time'),
    })

    # TODO actually change loaders to load this based on stuff
    return HttpResponse(render_response_search(request,
                        'tardis_portal/experiment/list_mine.html', c))


@login_required
def experiment_list_shared(request):

    c = Context({
        'subtitle': 'Shared Experiments',
        'can_see_private': True,
        'experiments': authz.get_shared_experiments(request)
                            .order_by('-update_time'),
    })

    # TODO actually change loaders to load this based on stuff
    return HttpResponse(render_response_search(request,
                        'tardis_portal/experiment/list_shared.html', c))


def experiment_list_public(request):

    private_filter = Q(public_access=Experiment.PUBLIC_ACCESS_NONE)

    c = Context({
        'subtitle': 'Public Experiments',
        'can_see_private': False,
        'experiments': Experiment.objects.exclude(private_filter)
                                         .order_by('-update_time'),
    })

    return HttpResponse(render_response_search(request,
                        'tardis_portal/experiment/list_public.html', c))


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
    c = Context({})

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
            if ns in namespaces:
                x = view_fn.split(".")
                mod_name, fn_name = (".".join(x[:-1]), x[-1])
                try:
                    module = __import__(mod_name, fromlist=[fn_name])
                    fn = getattr(module, fn_name)
                    return fn(request, experiment_id=experiment_id)
                except (ImportError, AttributeError) as e:
                    logger.error('custom view import failed. view name: %s, '
                                 'error-msg: %s' % (repr(view_fn), e))
                    continue

    c['experiment'] = experiment
    c['has_write_permissions'] = \
        authz.has_write_permissions(request, experiment_id)
    c['has_download_permissions'] = \
        authz.has_experiment_download_access(request, experiment_id)
    if request.user.is_authenticated():
        c['is_owner'] = authz.has_experiment_ownership(request, experiment_id)
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

    import sys
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


@authz.experiment_access_required
def experiment_description(request, experiment_id):
    """View an existing experiment's description. To be loaded via ajax.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param experiment_id: the ID of the experiment to be edited
    :type experiment_id: string
    :rtype: :class:`django.http.HttpResponse`

    """
    c = Context({})

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

    c['authors'] = experiment.author_experiment_set.all()

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


class SearchQueryString():
    """
    Class to manage switching between space separated search queries and
    '+' separated search queries (for addition to urls

    TODO This would probably be better handled with filters
    """

    def __init__(self, query_string):
        import re
        # remove extra spaces around colons
        stripped_query = re.sub('\s*?:\s*', ':', query_string)

        # create a list of terms which can be easily joined by
        # spaces or pluses
        self.query_terms = stripped_query.split()

    def __unicode__(self):
        return ' '.join(self.query_terms)

    def url_safe_query(self):
        return '+'.join(self.query_terms)

    def query_string(self):
        return self.__unicode__()


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
                    continue

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

    c = Context({
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
    })
    _add_protocols_and_organizations(request, dataset, c)
    return HttpResponse(render_response_index(
        request, 'tardis_portal/view_dataset.html', c))


@never_cache
@authz.experiment_access_required
def experiment_datasets(request, experiment_id):
    return view_experiment(
        request, experiment_id=experiment_id,
        template_name='tardis_portal/ajax/experiment_datasets.html')


@never_cache  # too complex # noqa
@authz.dataset_access_required
def dataset_json(request, experiment_id=None, dataset_id=None):
    # Experiment ID is optional (but dataset_id is not)!
    dataset = Dataset.objects.get(id=dataset_id)

    if experiment_id:
        try:
            # PUT is fine for non-existing resources, but GET/DELETE is not
            if request.method == 'PUT':
                experiment = Experiment.objects.get(id=experiment_id)
            else:
                experiment = dataset.experiments.get(id=experiment_id)
        except Experiment.DoesNotExist:
            return HttpResponseNotFound()

    # Convenience methods for permissions
    def can_update():
        return authz.has_dataset_ownership(request, dataset_id)
    can_delete = can_update

    def add_experiments(updated_experiments):
        current_experiments = \
            frozenset(dataset.experiments.values_list('id', flat=True))
        # Get all the experiments that currently aren't associated
        for experiment_id in updated_experiments - current_experiments:
            # You must own the experiment to assign datasets to it
            if authz.has_experiment_ownership(request, experiment_id):
                experiment = Experiment.safe.get(request.user, experiment_id)
                logger.info("Adding dataset #%d to experiment #%d" %
                            (dataset.id, experiment.id))
                dataset.experiments.add(experiment)

    # Update this experiment to add it to more experiments
    if request.method == 'PUT':
        # Obviously you can't do this if you don't own the dataset
        if not can_update():
            return HttpResponseForbidden()
        data = json.loads(request.body)
        # Detect if any experiments are new, and add the dataset to them
        add_experiments(frozenset(data['experiments']))
        # Include the experiment we PUT to, as it may also be new
        if experiment is not None:
            add_experiments(frozenset((experiment.id,)))
        dataset.save()

    # Remove this dataset from the given experiment
    if request.method == 'DELETE':
        # First, we need an experiment
        if experiment_id is None:
            # As the experiment is in the URL, this method will never be
            # allowed
            if can_update():
                return HttpResponseMethodNotAllowed(allow="GET PUT")
            return HttpResponseMethodNotAllowed(allow="GET")
        # Cannot remove if this is the last experiment
        if not can_delete() or dataset.experiments.count() < 2:
            return HttpResponseForbidden()
        dataset.experiments.remove(experiment)
        dataset.save()

    has_download_permissions = \
        authz.has_dataset_download_access(request, dataset_id)

    return HttpResponse(json.dumps(get_dataset_info(dataset,
                                                    has_download_permissions)),
                        mimetype='application/json')


@never_cache
@authz.experiment_access_required
def experiment_datasets_json(request, experiment_id):
    try:
        experiment = Experiment.safe.get(request.user, experiment_id)
    except Experiment.DoesNotExist:
        return return_response_not_found(request)

    has_download_permissions = \
        authz.has_experiment_download_access(request, experiment_id)

    objects = [
        get_dataset_info(ds, include_thumbnail=has_download_permissions,
                         exclude=['datafiles'])
        for ds in experiment.datasets.all()]

    return HttpResponse(json.dumps(objects), mimetype='application/json')


@never_cache
@authz.experiment_access_required
def experiment_dataset_transfer(request, experiment_id):
    experiments = Experiment.safe.owned(request.user)

    def get_json_url_pattern():
        placeholder = '314159'
        return reverse('tardis.tardis_portal.views.experiment_datasets_json',
                       args=[placeholder]).replace(placeholder,
                                                   '{{experiment_id}}')

    c = Context({'experiments': experiments.exclude(id=experiment_id),
                 'url_pattern': get_json_url_pattern()
                 })
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

    c = Context({'dataset': dataset,
                 'parametersets': parametersets,
                 'has_write_permissions': has_write_permissions})
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

    c = Context({'experiment': experiment,
                 'parametersets': parametersets,
                 'has_write_permissions': has_write_permissions})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/experiment_metadata.html', c))


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

    c = Context({
        'subtitle': 'Create Experiment',
        'user_id': request.user.id,
        })

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

    c = Context({'subtitle': 'Edit Experiment',
                 'experiment_id': experiment_id, })

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


# todo complete....
def login(request):
    '''
    handler for login page
    '''
    from tardis.tardis_portal.auth import auth_service

    if request.user.is_authenticated():
        # redirect the user to the home page if he is trying to go to the
        # login page
        return HttpResponseRedirect(request.POST.get('next_page', '/'))

    # TODO: put me in SETTINGS
    if 'username' in request.POST and \
            'password' in request.POST:
        authMethod = request.POST.get('authMethod', None)

        user = auth_service.authenticate(
            authMethod=authMethod, request=request)

        if user:
            next_page = request.POST.get(
                'next_page', request.GET.get('next_page', '/'))
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            djauth.login(request, user)
            return HttpResponseRedirect(next_page)

        c = Context({'status': "Sorry, username and password don't match.",
                     'error': True,
                     'loginForm': LoginForm()})

        return HttpResponseForbidden(
            render_response_index(request, 'tardis_portal/login.html', c))

    url = request.META.get('HTTP_REFERER', '/')
    u = urlparse(url)
    if u.netloc == request.META.get('HTTP_HOST', ""):
        next_page = u.path
    else:
        next_page = '/'
    c = Context({'loginForm': LoginForm(),
                 'next_page': next_page})

    c['RAPID_CONNECT_ENABLED'] = settings.RAPID_CONNECT_ENABLED
    c['RAPID_CONNECT_LOGIN_URL'] = settings.RAPID_CONNECT_CONFIG[
        'authnrequest_url']

    return HttpResponse(render_response_index(request,
                        'tardis_portal/login.html', c))


@permission_required('tardis_portal.change_userauthentication')
@login_required()
def manage_auth_methods(request):
    '''Manage the user's authentication methods using AJAX.'''
    from tardis.tardis_portal.auth.authentication import add_auth_method, \
        merge_auth_method, remove_auth_method, edit_auth_method, \
        list_auth_methods

    if request.method == 'POST':
        operation = request.POST['operation']
        if operation == 'addAuth':
            return add_auth_method(request)
        elif operation == 'mergeAuth':
            return merge_auth_method(request)
        elif operation == 'removeAuth':
            return remove_auth_method(request)
        else:
            return edit_auth_method(request)
    else:
        # if GET, we'll just give the initial list of auth methods for the user
        return list_auth_methods(request)


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
    context = Context({
        'datafile_id': datafile_id,
        'views': views,
    })
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

    c = Context({'parametersets': parametersets,
                 'datafile': datafile,
                 'has_write_permissions': has_write_permissions,
                 'has_download_permissions':
                 authz.has_dataset_download_access(request, dataset_id)})

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

    params = urlencode(params)

    c = Context({
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
        'params': params

        })
    _add_protocols_and_organizations(request, None, c)
    return HttpResponse(render_response_index(request, template_name, c))


@login_required()
def control_panel(request):

    experiments = Experiment.safe.owned(request.user)
    if experiments:
        experiments = experiments.order_by('title')

    c = Context({'experiments': experiments,
                 'subtitle': 'Experiment Control Panel'})

    return HttpResponse(render_response_index(request,
                        'tardis_portal/control_panel.html', c))


@oracle_dbops_hack
def search_experiment(request):

    """Either show the search experiment form or the result of the search
    experiment query.

    """

    if len(request.GET) == 0:
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
    c = Context({'header': 'Search Experiment',
                 'experiments': results,
                 'bodyclass': bodyclass})
    url = 'tardis_portal/search_experiment_results.html'
    return HttpResponse(render_response_search(request, url, c))


def search_quick(request):
    get = False
    experiments = Experiment.objects.all().order_by('title')

    if 'results' in request.GET:
        get = True
        if 'quicksearch' in request.GET \
           and len(request.GET['quicksearch']) > 0:
            experiments = \
                experiments.filter(
                    title__icontains=request.GET['quicksearch']) | \
                experiments.filter(
                    institution_name__icontains=request.GET['quicksearch']) | \
                experiments.filter(
                    author_experiment__author__name__icontains=request.GET[
                        'quicksearch']) | \
                experiments.filter(
                    pdbid__pdbid__icontains=request.GET['quicksearch'])

            experiments = experiments.distinct()

            logger.debug(experiments)

    c = Context({'submitted': get, 'experiments': experiments,
                'subtitle': 'Search Experiments'})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/search_experiment.html', c))


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
            author_experiment__author__icontains=searchFilterData['creator'])

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
        c = Context({'header': 'Search Datafile',
                     'searchForm': searchForm})
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
    c = Context({'header': 'Search Datafile',
                 'searchForm': searchForm,
                 'modifiedSearchForm': modifiedSearchForm})
    return HttpResponse(render_response_search(request, url, c))


def __forwardToSearchExperimentFormPage(request):
    """Forward to the search experiment form page."""

    searchForm = __getSearchExperimentForm(request)

    c = Context({'searchForm': searchForm})
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


def search_datafile(request):  # too complex # noqa
    """Either show the search datafile form or the result of the search
    datafile query.

    """

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

    c = Context({
        'experiments': results,
        'datafiles': datafile_results,
        # 'paginator': paginator,
        'query_string': cleanedUpQueryString,
        'subtitle': 'Search Datafiles',
        'nav': [{'name': 'Search Datafile', 'link': '/search/datafile/'}],
        'bodyclass': bodyclass,
        'search_pressed': True,
        'searchDatafileSelectionForm': getNewSearchDatafileSelectionForm()})
    url = 'tardis_portal/search_experiment_results.html'
    return HttpResponse(render_response_search(request, url, c))


@never_cache
@login_required()
def retrieve_user_list(request):
    # TODO: Hook this up to authservice.searchUsers() to actually get
    # autocompletion data directly from auth backends.
    # The following local DB query would be moved to
    # auth.localdb_auth.SearchUsers.
    query = request.GET.get('q', '')
    limit = int(request.GET.get('limit', '10'))

    # Search all user fields and also the UserAuthentication username.
    q = Q(username__icontains=query) | \
        Q(email__icontains=query) | \
        Q(userprofile__userauthentication__username__icontains=query)

    # Tokenize query string so "Bob Sm" matches (first_name~=Bob &
    # last_name~=Smith).
    tokens = query.split()
    if len(tokens) < 2:
        q |= Q(first_name__icontains=query.strip())
        q |= Q(last_name__icontains=query.strip())
    else:
        q |= Q(first_name__icontains=' '.join(tokens[:-1])) &\
            Q(last_name__icontains=tokens[-1])

    q_tokenuser = Q(username=settings.TOKEN_USERNAME)
    users_query = User.objects\
                      .exclude(q_tokenuser)\
                      .filter(q).distinct() .select_related('userprofile')

    # HACK FOR ORACLE - QUERY GENERATED DOES NOT WORK WITH LIMIT SO USING
    # ITERATOR INSTEAD
    from itertools import islice
    first_n_users = list(islice(users_query, limit))

    user_auths = list(UserAuthentication.objects.filter(
        userProfile__user__in=first_n_users))
    auth_methods = dict((ap[0], ap[1]) for ap in settings.AUTH_PROVIDERS)
    """
    users = [ {
        "username": "ksr",
        "first_name": "Kieran",
        "last_name": "Spear",
        "email": "email@address.com",
        "auth_methods": [ "ksr:vbl:VBL", "ksr:localdb:Local DB" ]
    } , ... ]
    """
    users = []
    for u in users_query:
        fields = ('first_name', 'last_name', 'username', 'email')
        # Convert attributes to dictionary keys and make sure all values
        # are strings.
        user = dict([(k, str(getattr(u, k))) for k in fields])
        try:
            user['auth_methods'] = [
                '%s:%s:%s' %
                (ua.username, ua.authenticationMethod,
                 auth_methods[ua.authenticationMethod])
                for ua in user_auths if ua.userProfile == u.get_profile()]
        except UserProfile.DoesNotExist:
            user['auth_methods'] = []

        if not user['auth_methods']:
            user['auth_methods'] = ['%s:localdb:%s' %
                                    (u.username, auth_methods['localdb'])]
        users.append(user)

    users.sort(key=itemgetter('first_name'))
    return HttpResponse(json.dumps(users))


@never_cache
@login_required()
def retrieve_group_list(request):

    grouplist = ' ~ '.join(map(str, Group.objects.all().order_by('name')))
    return HttpResponse(grouplist)


def retrieve_field_list(request):

    from tardis.tardis_portal.search_indexes import DatasetFileIndex

    # Get all of the fields in the indexes
    #
    # TODO: these should be onl read from registered indexes
    #
    allFields = DatasetFileIndex.fields.items()

    users = User.objects.all()

    usernames = [u.first_name + ' ' + u.last_name + ':username' for u in users]

    # Collect all of the indexed (searchable) fields, except
    # for the main search document ('text')
    searchableFields = ([key + ':search_field' for key, f in allFields
                         if f.indexed is True and key != 'text'])

    auto_list = usernames + searchableFields

    fieldList = '+'.join([str(fn) for fn in auto_list])
    return HttpResponse(fieldList)


@never_cache
@authz.experiment_ownership_required
def retrieve_access_list_user(request, experiment_id):
    from tardis.tardis_portal.forms import AddUserPermissionsForm
    user_acls = Experiment.safe.user_acls(experiment_id)

    c = Context({'user_acls': user_acls, 'experiment_id': experiment_id,
                 'addUserPermissionsForm': AddUserPermissionsForm()})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/access_list_user.html', c))


@never_cache
def retrieve_access_list_user_readonly(request, experiment_id):
    user_acls = Experiment.safe.user_acls(experiment_id)

    c = Context({'user_acls': user_acls, 'experiment_id': experiment_id})
    return HttpResponse(
        render_response_index(
            request, 'tardis_portal/ajax/access_list_user_readonly.html', c))


@never_cache
@authz.experiment_ownership_required
def retrieve_access_list_group(request, experiment_id):

    from tardis.tardis_portal.forms import AddGroupPermissionsForm

    group_acls_system_owned = Experiment.safe.group_acls_system_owned(
        experiment_id)

    group_acls_user_owned = Experiment.safe.group_acls_user_owned(
        experiment_id)

    c = Context({'group_acls_user_owned': group_acls_user_owned,
                 'group_acls_system_owned': group_acls_system_owned,
                 'experiment_id': experiment_id,
                 'addGroupPermissionsForm': AddGroupPermissionsForm()})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/access_list_group.html', c))


@never_cache
def retrieve_access_list_group_readonly(request, experiment_id):

    group_acls_system_owned = Experiment.safe.group_acls_system_owned(
        experiment_id)

    group_acls_user_owned = Experiment.safe.group_acls_user_owned(
        experiment_id)

    c = Context({'experiment_id': experiment_id,
                 'group_acls_system_owned': group_acls_system_owned,
                 'group_acls_user_owned': group_acls_user_owned})
    return HttpResponse(render_response_index(
        request,
        'tardis_portal/ajax/access_list_group_readonly.html', c))


@never_cache
@authz.experiment_ownership_required
def retrieve_access_list_external(request, experiment_id):

    groups = Experiment.safe.external_users(experiment_id)
    c = Context({'groups': groups, 'experiment_id': experiment_id})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/access_list_external.html', c))


@never_cache
@authz.experiment_download_required
def retrieve_access_list_tokens(request, experiment_id):
    tokens = Token.objects.filter(experiment=experiment_id)

    def token_url(token):
        url = request.META['HTTP_REFERER']
        u = urlparse(url)
        query = parse_qs(u.query)
        query.pop('token', None)
        query['token'] = token.token
        u = u._replace(query=urlencode(query, True))
        return u.geturl()
        # return '%s?token=%s' % (request.META['HTTP_REFERER'], token.token)
    tokens = [{'expiry_date': token.expiry_date,
               'user': token.user,
               'url': request.build_absolute_uri(token_url(token)),
               'id': token.id,
               'experiment_id': experiment_id,
               'is_owner': request.user.has_perm('tardis_acls.owns_experiment',
                                                 token.experiment),
               } for token in tokens]
    c = Context({'tokens': tokens})
    return HttpResponse(render_response_index(
        request, 'tardis_portal/ajax/access_list_tokens.html', c))


@never_cache
@authz.group_ownership_required
def retrieve_group_userlist(request, group_id):

    from tardis.tardis_portal.forms import ManageGroupPermissionsForm
    users = User.objects.filter(groups__id=group_id)
    c = Context({'users': users, 'group_id': group_id,
                 'manageGroupPermissionsForm': ManageGroupPermissionsForm()})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/group_user_list.html', c))


@never_cache
def retrieve_group_userlist_readonly(request, group_id):

    from tardis.tardis_portal.forms import ManageGroupPermissionsForm
    users = User.objects.filter(groups__id=group_id)
    c = Context({'users': users, 'group_id': group_id,
                 'manageGroupPermissionsForm': ManageGroupPermissionsForm()})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/group_user_list_readonly.html', c))


@never_cache
def retrieve_group_list_by_user(request):

    groups = Group.objects.filter(groupadmin__user=request.user)
    c = Context({'groups': groups})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/group_list.html', c))


@never_cache
@permission_required('auth.change_group')
@login_required()
def manage_groups(request):

    c = Context({})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/manage_group_members.html', c))


@never_cache  # too complex # noqa
@authz.group_ownership_required
def add_user_to_group(request, group_id, username):

    if username == settings.TOKEN_USERNAME:
        return HttpResponse('User does not exist: %s' % username)

    authMethod = localdb_auth_key
    isAdmin = False

    if 'isAdmin' in request.GET:
        if request.GET['isAdmin'] == 'true':
            isAdmin = True

    try:
        authMethod = request.GET['authMethod']
        if authMethod == localdb_auth_key:
            user = User.objects.get(username=username)
        else:
            user = UserAuthentication.objects.get(
                username=username,
                authenticationMethod=authMethod).userProfile.user
    except User.DoesNotExist:
        return return_response_error(request)
    except UserAuthentication.DoesNotExist:
        return return_response_error(request)

    try:
        group = Group.objects.get(pk=group_id)
    except Group.DoesNotExist:
        return HttpResponse('Group does not exist.')

    if user.groups.filter(name=group.name).count() > 0:
        return HttpResponse('User %s is already member of that group.'
                            % username)

    user.groups.add(group)
    user.save()

    if isAdmin:
        groupadmin = GroupAdmin(user=user, group=group)
        groupadmin.save()

    c = Context({'user': user, 'group_id': group_id, 'isAdmin': isAdmin})
    return HttpResponse(render_response_index(
        request,
        'tardis_portal/ajax/add_user_to_group_result.html', c))


@never_cache
@authz.group_ownership_required
def remove_user_from_group(request, group_id, username):

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse('User %s does not exist.' % username)
    try:
        group = Group.objects.get(pk=group_id)
    except Group.DoesNotExist:
        return HttpResponse('Group does not exist.')

    if user.groups.filter(name=group.name).count() == 0:
        return HttpResponse('User %s is not member of that group.'
                            % username)

    if request.user == user:
        return HttpResponse('You cannot remove yourself from that group.')

    user.groups.remove(group)
    user.save()

    try:
        groupadmin = GroupAdmin.objects.filter(user=user, group=group)
        groupadmin.delete()
    except GroupAdmin.DoesNotExist:
        pass

    return HttpResponse('OK')


@never_cache  # too complex # noqa
@transaction.commit_on_success
@authz.experiment_ownership_required
def add_experiment_access_user(request, experiment_id, username):

    canRead = False
    canWrite = False
    canDelete = False
    isOwner = False

    if 'canRead' in request.GET:
        if request.GET['canRead'] == 'true':
            canRead = True

    if 'canWrite' in request.GET:
        if request.GET['canWrite'] == 'true':
            canWrite = True

    if 'canDelete' in request.GET:
        if request.GET['canDelete'] == 'true':
            canDelete = True

    if 'isOwner' in request.GET:
        if request.GET['isOwner'] == 'true':
            isOwner = True

    authMethod = request.GET['authMethod']
    user = auth_service.getUser(authMethod, username)
    if user is None or username == settings.TOKEN_USERNAME:
        return HttpResponse('User %s does not exist.' % (username))

    try:
        experiment = Experiment.objects.get(pk=experiment_id)
    except Experiment.DoesNotExist:
        return HttpResponse('Experiment (id=%d) does not exist.'
                            % (experiment.id))

    acl = ObjectACL.objects.filter(
        content_type=experiment.get_ct(),
        object_id=experiment.id,
        pluginId=django_user,
        entityId=str(user.id),
        aclOwnershipType=ObjectACL.OWNER_OWNED)

    if acl.count() == 0:
        acl = ObjectACL(content_object=experiment,
                        pluginId=django_user,
                        entityId=str(user.id),
                        canRead=canRead,
                        canWrite=canWrite,
                        canDelete=canDelete,
                        isOwner=isOwner,
                        aclOwnershipType=ObjectACL.OWNER_OWNED)

        acl.save()
        c = Context({'authMethod': authMethod,
                     'user': user,
                     'user_acl': acl,
                     'username': username,
                     'experiment_id': experiment_id})

        return HttpResponse(render_response_index(
            request,
            'tardis_portal/ajax/add_user_result.html', c))

    return HttpResponse('User already has experiment access.')


@never_cache
@authz.experiment_ownership_required
def remove_experiment_access_user(request, experiment_id, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse('User %s does not exist' % username)

    try:
        experiment = Experiment.objects.get(pk=experiment_id)
    except Experiment.DoesNotExist:
        return HttpResponse('Experiment does not exist')

    acl = ObjectACL.objects.filter(
        content_type=experiment.get_ct(),
        object_id=experiment.id,
        pluginId=django_user,
        entityId=str(user.id),
        aclOwnershipType=ObjectACL.OWNER_OWNED)

    if acl.count() == 1:
        if int(acl[0].entityId) == request.user.id:
            return HttpResponse('Cannot remove your own user access.')

        acl[0].delete()
        return HttpResponse('OK')
    elif acl.count() == 0:
        return HttpResponse(
            'The user %s does not have access to this experiment.' % username)
    else:
        return HttpResponse('Multiple ACLs found')


@never_cache
@authz.experiment_ownership_required
def change_user_permissions(request, experiment_id, username):

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return return_response_error(request)

    try:
        experiment = Experiment.objects.get(pk=experiment_id)
    except Experiment.DoesNotExist:
        return return_response_error(request)

    try:
        acl = ObjectACL.objects.get(
            content_type=experiment.get_ct(),
            object_id=experiment.id,
            pluginId=django_user,
            entityId=str(user.id),
            aclOwnershipType=ObjectACL.OWNER_OWNED)
    except ObjectACL.DoesNotExist:
        return return_response_error(request)

    if request.method == 'POST':
        form = ChangeUserPermissionsForm(request.POST, instance=acl)

        if form.is_valid:
            form.save()
            url = reverse('tardis.tardis_portal.views.control_panel')
            return HttpResponseRedirect(url)

    else:
        form = ChangeUserPermissionsForm(instance=acl)
        c = Context({'form': form,
                     'header':
                     "Change User Permissions for '%s'" % user.username})

    return HttpResponse(render_response_index(
        request, 'tardis_portal/form_template.html', c))


@never_cache
@authz.experiment_ownership_required
def change_group_permissions(request, experiment_id, group_id):

    try:
        group = Group.objects.get(pk=group_id)
    except Group.DoesNotExist:
        return return_response_error(request)

    try:
        experiment = Experiment.objects.get(pk=experiment_id)
    except Experiment.DoesNotExist:
        return return_response_error(request)

    try:
        acl = ObjectACL.objects.get(
            content_type=experiment.get_ct(),
            object_id=experiment.id,
            pluginId='django_group',
            entityId=str(group.id),
            aclOwnershipType=ObjectACL.OWNER_OWNED)
    except ObjectACL.DoesNotExist:
        return return_response_error(request)

    if request.method == 'POST':
        form = ChangeGroupPermissionsForm(request.POST)

        if form.is_valid():
            acl.canRead = form.cleaned_data['canRead']
            acl.canWrite = form.cleaned_data['canWrite']
            acl.canDelete = form.cleaned_data['canDelete']
            acl.effectiveDate = form.cleaned_data['effectiveDate']
            acl.expiryDate = form.cleaned_data['expiryDate']
            acl.save()
            return HttpResponseRedirect('/experiment/control_panel/')

    else:
        form = ChangeGroupPermissionsForm(
            initial={'canRead': acl.canRead,
                     'canWrite': acl.canWrite,
                     'canDelete': acl.canDelete,
                     'effectiveDate': acl.effectiveDate,
                     'expiryDate': acl.expiryDate})

    c = Context({'form': form,
                 'header': "Change Group Permissions for '%s'" % group.name})

    return HttpResponse(render_response_index(
        request, 'tardis_portal/form_template.html', c))


@transaction.commit_on_success  # too complex # noqa
@never_cache
def create_group(request):

    if 'group' not in request.GET:
        c = Context({'createGroupPermissionsForm':
                     CreateGroupPermissionsForm()})

        response = HttpResponse(render_response_index(
            request,
            'tardis_portal/ajax/create_group.html', c))
        return response

    authMethod = localdb_auth_key
    admin = None
    groupname = None

    if 'group' in request.GET:
        groupname = request.GET['group']

    if 'admin' in request.GET:
        admin = request.GET['admin']

    if 'authMethod' in request.GET:
        authMethod = request.GET['authMethod']

    try:
        group = Group(name=groupname)
        group.save()
    except:
        transaction.rollback()
        return HttpResponse('Could not create group %s '
                            '(It is likely that it already exists)' %
                            (groupname))

    adminuser = None
    if admin:
        if admin == settings.TOKEN_USERNAME:
            transaction.rollback()
            return HttpResponse('User %s does not exist' %
                                (settings.TOKEN_USERNAME))
        try:
            authMethod = request.GET['authMethod']
            if authMethod == localdb_auth_key:
                adminuser = User.objects.get(username=admin)
            else:
                adminuser = UserAuthentication.objects.get(
                    username=admin,
                    authenticationMethod=authMethod).userProfile.user

        except User.DoesNotExist:
            transaction.rollback()
            return HttpResponse('User %s does not exist' % (admin))
        except UserAuthentication.DoesNotExist:
            transaction.rollback()
            return HttpResponse('User %s does not exist' % (admin))

        # create admin for this group and add it to the group
        groupadmin = GroupAdmin(user=adminuser, group=group)
        groupadmin.save()

        adminuser.groups.add(group)
        adminuser.save()

    # add the current user as admin as well for newly created groups
    if not request.user == adminuser:
        user = request.user

        groupadmin = GroupAdmin(user=user, group=group)
        groupadmin.save()

        user.groups.add(group)
        user.save()

    c = Context({'group': group})
    transaction.commit()

    response = HttpResponse(render_response_index(
        request,
        'tardis_portal/ajax/create_group.html', c))
    return response


@never_cache  # too complex # noqa
@transaction.commit_manually
@authz.experiment_ownership_required
def add_experiment_access_group(request, experiment_id, groupname):

    canRead = False
    canWrite = False
    canDelete = False
    isOwner = False

    if 'canRead' in request.GET:
        if request.GET['canRead'] == 'true':
            canRead = True

    if 'canWrite' in request.GET:
        if request.GET['canWrite'] == 'true':
            canWrite = True

    if 'canDelete' in request.GET:
        if request.GET['canDelete'] == 'true':
            canDelete = True

    if 'isOwner' in request.GET:
        if request.GET['isOwner'] == 'true':
            isOwner = True

    try:
        experiment = Experiment.objects.get(pk=experiment_id)
    except Experiment.DoesNotExist:
        transaction.rollback()
        return HttpResponse('Experiment (id=%d) does not exist' %
                            (experiment_id))

    try:
        group = Group.objects.get(name=groupname)
    except Group.DoesNotExist:
        transaction.rollback()
        return HttpResponse('Group %s does not exist' % (groupname))

    acl = ObjectACL.objects.filter(
        content_type=experiment.get_ct(),
        object_id=experiment.id,
        pluginId='django_group',
        entityId=str(group.id),
        aclOwnershipType=ObjectACL.OWNER_OWNED)

    if acl.count() > 0:
        # An ACL already exists for this experiment/group.
        transaction.rollback()
        return HttpResponse('Could not create group %s '
                            '(It is likely that it already exists)' %
                            (groupname))

    acl = ObjectACL(content_object=experiment,
                    pluginId='django_group',
                    entityId=str(group.id),
                    canRead=canRead,
                    canWrite=canWrite,
                    canDelete=canDelete,
                    isOwner=isOwner,
                    aclOwnershipType=ObjectACL.OWNER_OWNED)
    acl.save()

    c = Context({'group': group,
                'group_acl': acl,
                 'experiment_id': experiment_id})
    response = HttpResponse(render_response_index(
        request,
        'tardis_portal/ajax/add_group_result.html', c))
    transaction.commit()
    return response


@never_cache
@authz.experiment_ownership_required
def remove_experiment_access_group(request, experiment_id, group_id):

    try:
        group = Group.objects.get(pk=group_id)
    except Group.DoesNotExist:
        return HttpResponse('Group does not exist')

    try:
        experiment = Experiment.objects.get(pk=experiment_id)
    except Experiment.DoesNotExist:
        return HttpResponse('Experiment does not exist')

    acl = ObjectACL.objects.filter(
        content_type=experiment.get_ct(),
        object_id=experiment.id,
        pluginId='django_group',
        entityId=str(group.id),
        aclOwnershipType=ObjectACL.OWNER_OWNED)

    if acl.count() == 1:
        acl[0].delete()
        return HttpResponse('OK')
    elif acl.count() == 0:
        return HttpResponse('No ACL available.'
                            'It is likely the group doesnt have access to'
                            'this experiment.')
    else:
        return HttpResponse('Multiple ACLs found')

    return HttpResponse('')


def stats(request):
    # using count() is more efficient than using len() on a query set
    cursor = connection.cursor()
    if cursor.db.vendor == 'postgresql':
        cursor.execute("SELECT SUM(size::bigint) FROM tardis_portal_datafile")
        datafile_size = int(cursor.fetchone()[0])
    else:
        datafile_size = DataFile.sum_sizes(DataFile.objects.all())
    c = Context({
        'experiment_count': Experiment.objects.all().count(),
        'dataset_count': Dataset.objects.all().count(),
        'datafile_count': DataFile.objects.all().count(),
        'datafile_size': datafile_size,
    })
    return HttpResponse(render_response_index(request,
                        'tardis_portal/stats.html', c))


@transaction.commit_on_success  # too complex # noqa
@never_cache
def create_user(request):

    if 'user' not in request.POST:
        c = Context({'createUserPermissionsForm':
                     CreateUserPermissionsForm()})

        response = HttpResponse(render_response_index(
            request,
            'tardis_portal/ajax/create_user.html', c))
        return response

    authMethod = localdb_auth_key

    if 'user' in request.POST:
        username = request.POST['user']

    if 'authMethod' in request.POST:
        authMethod = request.POST['authMethod']

    if 'email' in request.POST:
        email = request.POST['email']

    if 'password' in request.POST:
        password = request.POST['password']

    try:
        validate_email(email)

        user = User.objects.create_user(username, email, password)

        userProfile = UserProfile(user=user, isDjangoAccount=True)
        userProfile.save()

        authentication = UserAuthentication(userProfile=userProfile,
                                            username=username,
                                            authenticationMethod=authMethod)
        authentication.save()

    except ValidationError:
        return HttpResponse('Could not create user %s '
                            '(Email address is invalid: %s)' %
                            (username, email), status=403)
    except:
        transaction.rollback()
        return HttpResponse(
            'Could not create user %s '
            '(It is likely that this username already exists)' %
            (username), status=403)

    c = Context({'user_created': username})
    transaction.commit()

    response = HttpResponse(render_response_index(
        request,
        'tardis_portal/ajax/create_user.html', c))
    return response


def upload_complete(request,
                    template_name='tardis_portal/upload_complete.html'):
    """
    The ajax-loaded result of a file being uploaded

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param template_name: the path of the template to render
    :type template_name: string
    :rtype: :class:`django.http.HttpResponse`
    """

    c = Context({
        'numberOfFiles': request.POST['filesUploaded'],
        'bytes': request.POST['allBytesLoaded'],
        'speed': request.POST['speed'],
        'errorCount': request.POST['errorCount'],
        })
    return render_to_response(template_name, c)


@authz.upload_auth
@authz.dataset_write_permissions_required
def upload(request, dataset_id):
    """
    Uploads a datafile to the store and datafile metadata

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param dataset_id: the dataset_id
    :type dataset_id: integer
    :returns: boolean true if successful
    :rtype: bool
    """

    dataset = Dataset.objects.get(id=dataset_id)

    logger.debug('called upload')
    if request.method == 'POST':
        logger.debug('got POST')
        if request.FILES:

            uploaded_file_post = request.FILES['Filedata']
            logger.debug('done upload')
            md5, sha512, size, mimetype_buffer = generate_file_checksums(
                uploaded_file_post)
            datafile = DataFile(dataset=dataset,
                                filename=uploaded_file_post.name,
                                size=uploaded_file_post.size,
                                md5sum=md5,
                                sha512sum=sha512)
            datafile.save(require_checksums=False)
            logger.debug('created file')
            datafile.file_object = uploaded_file_post
            logger.debug('saved datafile')

    return HttpResponse('True')


@authz.dataset_write_permissions_required
def import_staging_files(request, dataset_id):
    """
    Creates an jstree view of the staging area of the user, and provides
    a selection mechanism importing files.
    """

    staging = get_full_staging_path(request.user.username)
    if not staging:
        return HttpResponseNotFound()

    c = Context({
        'dataset_id': dataset_id,
        'staging_mount_prefix': settings.STAGING_MOUNT_PREFIX,
        'staging_mount_user_suffix_enable':
        settings.STAGING_MOUNT_USER_SUFFIX_ENABLE,
    })
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

    c = Context({
        'dataset_id': dataset_id,
        'directory_listing': staging_list(from_path, staging, root=root),
    })
    return HttpResponse(render(
        request, 'tardis_portal/ajax/list_staging_files.html', c))


@authz.dataset_write_permissions_required
def upload_files(request, dataset_id,
                 template_name='tardis_portal/ajax/upload_files.html'):
    """
    Creates an Uploadify 'create files' button with a dataset
    destination. `A workaround for a JQuery Dialog conflict\
    <http://www.uploadify.com/forums/discussion/3348/
        uploadify-in-jquery-ui-dialog-modal-causes-double-queue-item/p1>`_

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param template_name: the path of the template to render
    :param dataset_id: the dataset_id
    :type dataset_id: integer
    :returns: A view containing an Uploadify *create files* button
    """
    if 'message' in request.GET:
        message = request.GET['message']
    else:
        message = "Upload Files to Dataset"
    url = reverse('tardis.tardis_portal.views.upload_complete')
    c = Context({'upload_complete_url': url,
                 'dataset_id': dataset_id,
                 'message': message,
                 'session_id': request.session.session_key
                 })
    return render_to_response(template_name, c)


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


@login_required
def edit_experiment_par(request, parameterset_id):
    parameterset = ExperimentParameterSet.objects.get(id=parameterset_id)
    if authz.has_write_permissions(request, parameterset.experiment.id):
        return edit_parameters(request, parameterset, otype="experiment")
    else:
        return return_response_error(request)


@login_required
def edit_dataset_par(request, parameterset_id):
    parameterset = DatasetParameterSet.objects.get(id=parameterset_id)
    if authz.has_dataset_write(request, parameterset.dataset.id):
        return edit_parameters(request, parameterset, otype="dataset")
    else:
        return return_response_error(request)


@login_required
def edit_datafile_par(request, parameterset_id):
    parameterset = DatafileParameterSet.objects.get(id=parameterset_id)
    if authz.has_dataset_write(request, parameterset.datafile.dataset.id):
        return edit_parameters(request, parameterset, otype="datafile")
    else:
        return return_response_error(request)


def edit_parameters(request, parameterset, otype):

    parameternames = ParameterName.objects.filter(
        schema__namespace=parameterset.schema.namespace)
    success = False
    valid = True

    if request.method == 'POST':
        request = remove_csrf_token(request)

        class DynamicForm(create_parameterset_edit_form(
                parameterset, request=request)):
            pass

        form = DynamicForm(request.POST)

        if form.is_valid():
            save_datafile_edit_form(parameterset, request)

            success = True
        else:
            valid = False

    else:

        class DynamicForm(create_parameterset_edit_form(
                parameterset)):
            pass

        form = DynamicForm()

    c = Context({
        'schema': parameterset.schema,
        'form': form,
        'parameternames': parameternames,
        'type': otype,
        'success': success,
        'parameterset_id': parameterset.id,
        'valid': valid,
    })

    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/parameteredit.html', c))


@login_required
def add_datafile_par(request, datafile_id):
    parentObject = DataFile.objects.get(id=datafile_id)
    if authz.has_dataset_write(request, parentObject.dataset.id):
        return add_par(request, parentObject,
                       otype="datafile", stype=Schema.DATAFILE)
    else:
        return return_response_error(request)


@login_required
def add_dataset_par(request, dataset_id):
    parentObject = Dataset.objects.get(id=dataset_id)
    if authz.has_dataset_write(request, parentObject.id):
        return add_par(request, parentObject, otype="dataset",
                       stype=Schema.DATASET)
    else:
        return return_response_error(request)


@login_required
def add_experiment_par(request, experiment_id):
    parentObject = Experiment.objects.get(id=experiment_id)
    if authz.has_write_permissions(request, parentObject.id):
        return add_par(request, parentObject, otype="experiment",
                       stype=Schema.EXPERIMENT)
    else:
        return return_response_error(request)


def add_par(request, parentObject, otype, stype):

    all_schema = Schema.objects.filter(type=stype, immutable=False)

    if 'schema_id' in request.GET:
        schema_id = request.GET['schema_id']
    elif all_schema.count() > 0:
        schema_id = all_schema[0].id
    else:
        return HttpResponse(render_response_index(
            request, 'tardis_portal/ajax/parameter_set_unavailable.html', {}))

    schema = Schema.objects.get(id=schema_id)

    parameternames = ParameterName.objects.filter(
        schema__namespace=schema.namespace)

    success = False
    valid = True

    if request.method == 'POST':
        request = remove_csrf_token(request)

        class DynamicForm(create_datafile_add_form(
                schema.namespace, parentObject, request=request)):
            pass

        form = DynamicForm(request.POST)

        if form.is_valid():
            save_datafile_add_form(schema.namespace, parentObject, request)

            success = True
        else:
            valid = False

    else:

        class DynamicForm(create_datafile_add_form(
                schema.namespace, parentObject)):
            pass

        form = DynamicForm()

    c = Context({
        'schema': schema,
        'form': form,
        'parameternames': parameternames,
        'type': otype,
        'success': success,
        'valid': valid,
        'parentObject': parentObject,
        'all_schema': all_schema,
        'schema_id': schema.id,
    })

    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/parameteradd.html', c))


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
            [e.pk for e in Experiment.objects.exclude(
                public_access=Experiment.PUBLIC_ACCESS_NONE)])

        ids = list(set(experiment_ids) & set(access_list))
        experiments = Experiment.objects.filter(pk__in=ids)\
                                        .order_by('-update_time')

        results = []
        for e in experiments:
            result = {}
            result['sr'] = e
            result['dataset_hit'] = False
            result['datafile_hit'] = False
            result['experiment_hit'] = False
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


@login_required
def single_search(request):
    search_query = FacetFixedSearchQuery(backend=HighlightSearchBackend())
    sqs = SearchQuerySet(query=search_query)
    sqs.highlight()

    return ExperimentSearchView(
        template='search/search.html',
        searchqueryset=sqs,
        form_class=RawSearchForm,
    ).__call__(request)


def share(request, experiment_id):
    '''
    Choose access rights and licence.
    '''
    experiment = Experiment.objects.get(id=experiment_id)

    c = Context({})

    c['has_write_permissions'] = \
        authz.has_write_permissions(request, experiment_id)
    c['has_download_permissions'] = \
        authz.has_experiment_download_access(request, experiment_id)
    if request.user.is_authenticated():
        c['is_owner'] = authz.has_experiment_ownership(request, experiment_id)

    domain = Site.objects.get_current().domain
    public_link = experiment.public_access >= Experiment.PUBLIC_ACCESS_METADATA

    c['experiment'] = experiment
    c['public_link'] = public_link
    c['domain'] = domain

    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/share.html', c))


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
        c = Context({'no_valid_owner': True, 'experiment': experiment})
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

    c = Context({'form': form, 'experiment': experiment})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/choose_rights.html', c))


@require_POST
@authz.experiment_ownership_required
def create_token(request, experiment_id):
    experiment = Experiment.objects.get(id=experiment_id)
    token = Token(experiment=experiment, user=request.user)
    token.save_with_random_token()
    logger.info('created token: %s' % token)
    return HttpResponse('{"success": true}', mimetype='application/json')


@require_POST
def token_delete(request, token_id):
    token = Token.objects.get(id=token_id)
    if authz.has_experiment_ownership(request, token.experiment_id):
        token.delete()
        return HttpResponse('{"success": true}', mimetype='application/json')


def token_login(request, token):
    django_logout(request)

    from tardis.tardis_portal.auth import login, token_auth
    logger.debug('token login')

    user = token_auth.authenticate(request, token)
    if not user:
        return return_response_error(request)
    login(request, user)
    experiment = Experiment.objects.get(token__token=token)
    return HttpResponseRedirect(experiment.get_absolute_url())


@authz.experiment_access_required
def view_rifcs(request, experiment_id):
    """View the rif-cs of an existing experiment.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param experiment_id: the ID of the experiment to be viewed
    :type experiment_id: string
    :rtype: :class:`django.http.HttpResponse`

    """
    try:
        experiment = Experiment.safe.get(request.user, experiment_id)
    except PermissionDenied:
        return return_response_error(request)
    except Experiment.DoesNotExist:
        return return_response_not_found(request)

    try:
        rifcs_provs = settings.RIFCS_PROVIDERS
    except AttributeError:
        rifcs_provs = ()

    from tardis.tardis_portal.publish.publishservice import PublishService
    pservice = PublishService(rifcs_provs, experiment)
    context = pservice.get_context()
    if context is None:
        # return error page or something
        return return_response_error(request)

    template = pservice.get_template()
    return HttpResponse(render_response_index(request,
                        template, context), mimetype="text/xml")


def retrieve_licenses(request):
    try:
        type_ = int(request.REQUEST['public_access'])
        licenses = License.get_suitable_licenses(type_)
    except KeyError:
        licenses = License.get_suitable_licenses()
    return HttpResponse(json.dumps([model_to_dict(x) for x in licenses]))


def experiment_public_access_badge(request, experiment_id):
    try:
        experiment = Experiment.objects.get(id=experiment_id)
    except Experiment.DoesNotExist:
        HttpResponse('')

    if authz.has_experiment_access(request, experiment_id):
        return HttpResponse(render_public_access_badge(experiment))
    else:
        return HttpResponse('')


@login_required
def manage_user_account(request):
    user = request.user

    # Process form or prepopulate it
    if request.method == 'POST':
        form = ManageAccountForm(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            return _redirect_303('tardis.tardis_portal.views.index')
    else:
        form = ManageAccountForm(instance=user)

    c = Context({'form': form})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/manage_user_account.html', c))


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

    c = Context({'form': form})
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

    c = Context({'form': form, 'dataset': dataset})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/add_or_edit_dataset.html', c))


@login_required
def stage_files_to_dataset(request, dataset_id):
    """
    Takes a JSON list of filenames to import from the staging area to this
    dataset.
    """
    if not has_dataset_write(request, dataset_id):
        return HttpResponseForbidden()

    if request.method != 'POST':
        # This method only accepts POSTS, so send 405 Method Not Allowed
        response = HttpResponse(status=405)
        response['Allow'] = 'POST'
        return response

    user = request.user

    # Incoming data MUST be JSON
    if not request.META['CONTENT_TYPE'].startswith('application/json'):
        return HttpResponse(status=400)

    try:
        files = json.loads(request.body)
    except:
        return HttpResponse(status=400)

    create_staging_datafiles.delay(files, user.id, dataset_id,
                                   request.is_secure())

    email = {'email': user.email}
    return HttpResponse(json.dumps(email), status=201)


def user_guide(request):
    c = Context({})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/user_guide.html', c))


@csrf_exempt
def rcauth(request):
    # Only POST is supported on this URL.
    if request.method != 'POST':
        raise PermissionDenied

    # Rapid Connect authorization is disabled, so don't
    # process anything.
    if not settings.RAPID_CONNECT_ENABLED:
        raise PermissionDenied

    try:
        # Verifies signature and expiry time
        verified_jwt = jwt.decode(request.POST['assertion'],
                                  settings.RAPID_CONNECT_CONFIG['secret'])

        # Check for a replay attack using the jti value.
        jti = verified_jwt['jti']
        if JTI.objects.filter(jti=jti).exists():
            raise ValueError('Replay attack!')
        else:
            JTI(jti=jti).save()

        if verified_jwt['aud'] == settings.RAPID_CONNECT_CONFIG['aud'] and \
           verified_jwt['iss'] == settings.RAPID_CONNECT_CONFIG['iss']:
            request.session['attributes'] = verified_jwt[
                'https://aaf.edu.au/attributes']
            request.session['jwt'] = verified_jwt
            request.session['jws'] = request.POST['assertion']

            institution_email = request.session['attributes']['mail']

            logger.debug('Successfully authenticated %s via Rapid Connect.' %
                         institution_email)

            # Create a user account and profile automatically. In future,
            # support blacklists and whitelists.
            first_name = request.session['attributes']['givenname']
            c_name = request.session['attributes'].get('cn', '').split(' ')
            if not first_name and len(c_name) > 1:
                first_name = c_name[0]
            user_args = {
                'id': institution_email.lower(),
                'email': institution_email.lower(),
                'password': pwgen.pwgen(),
                'first_name': first_name,
                'last_name': request.session['attributes']['surname'],
            }
            user = auth_service.get_or_create_user(user_args)
            if user is not None:
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                djauth.login(request, user)
                return redirect('/')
        else:
            del request.session['attributes']
            del request.session['jwt']
            del request.session['jws']
            django_logout(request)
            raise PermissionDenied  # Error: Not for this audience
    except jwt.ExpiredSignature:
        del request.session['attributes']
        del request.session['jwt']
        del request.session['jws']
        django_logout(request)
        raise PermissionDenied  # Error: Security cookie has expired
