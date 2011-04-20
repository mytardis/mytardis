# -*- coding: utf-8 -*-
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

from base64 import b64decode
import urllib2
from urllib import urlencode, urlopen
from os import path

import logging

from django.template import Context
from django.conf import settings
from django.db import transaction
from django.shortcuts import render_to_response
from django.contrib.auth.models import User, Group, AnonymousUser
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.exceptions import PermissionDenied

from tardis.tardis_portal.ProcessExperiment import ProcessExperiment
from tardis.tardis_portal.forms import ExperimentForm, \
    createSearchDatafileForm, createSearchDatafileSelectionForm, \
    LoginForm, RegisterExperimentForm, createSearchExperimentForm, \
    ChangeGroupPermissionsForm, ChangeUserPermissionsForm, \
    ImportParamsForm, create_parameterset_edit_form, \
    save_datafile_edit_form, create_datafile_add_form,\
    save_datafile_add_form

from tardis.tardis_portal.errors import UnsupportedSearchQueryTypeError
from tardis.tardis_portal.staging import add_datafile_to_dataset,\
    staging_traverse, write_uploaded_file_to_dataset
from tardis.tardis_portal.models import Experiment, ExperimentParameter, \
    DatafileParameter, DatasetParameter, ExperimentACL, Dataset_File, \
    DatafileParameterSet, ParameterName, GroupAdmin, Schema, \
    Dataset, ExperimentParameterSet, DatasetParameterSet, \
    UserProfile, UserAuthentication

from tardis.tardis_portal import constants
from tardis.tardis_portal.auth.localdb_auth import django_user, django_group
from tardis.tardis_portal.auth.localdb_auth import auth_key as localdb_auth_key
from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.auth import auth_service
from tardis.tardis_portal.shortcuts import render_response_index, \
    return_response_error, return_response_not_found, \
    return_response_error_message, render_response_search
from tardis.tardis_portal.MultiPartForm import MultiPartForm
from tardis.tardis_portal.metsparser import parseMets


logger = logging.getLogger(__name__)


def getNewSearchDatafileSelectionForm(initial=None):
    DatafileSelectionForm = createSearchDatafileSelectionForm(initial)
    return DatafileSelectionForm()


def logout(request):
    if 'datafileResults' in request.session:
        del request.session['datafileResults']

    c = Context({})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/index.html', c))


def index(request):
    status = ''
    c = Context({'status': status})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/index.html', c))


def site_settings(request):

    if request.method == 'POST':
        if 'username' in request.POST and 'password' in request.POST:

            username = request.POST['username']
            password = request.POST['password']

            user = auth_service.authenticate(username=username,
                                             password=password,
                                             authMethod=localdb_auth_key)
            if user is not None:
                if user.is_staff:

                    x509 = open(settings.GRID_PROXY_FILE, 'r')

                    c = Context({'baseurl': request.build_absolute_uri('/'),
                        'proxy': x509.read(), 'filestorepath':
                        settings.FILE_STORE_PATH})
                    return HttpResponse(render_response_index(request,
                            'tardis_portal/site_settings.xml', c),
                            mimetype='application/xml')

    return return_response_error(request)


def load_image(request, experiment_id, parameter):
    from os.path import abspath, join
    file_path = abspath(join(settings.FILE_STORE_PATH,
                             str(experiment_id),
                             parameter.string_value))

    from django.core.servers.basehttp import FileWrapper
    wrapper = FileWrapper(file(file_path))
    return HttpResponse(wrapper, mimetype=parameter.name.units)


def load_experiment_image(request, parameter_id):
    parameter = ExperimentParameter.objects.get(pk=parameter_id)
    experiment_id = parameter.parameterset.experiment.id
    if authz.has_experiment_access(request, experiment_id):
        return load_image(request, experiment_id, parameter)
    else:
        return return_response_error(request)


def load_dataset_image(request, parameter_id):
    parameter = DatafileParameter.objects.get(pk=parameter_id)
    dataset = parameter.parameterset.dataset
    experiment_id = dataset.experiment.id
    if  authz.has_dataset_access(request, dataset.id):
        return load_image(request, experiment_id, parameter)
    else:
        return return_response_error(request)


def load_datafile_image(request, parameter_id):
    parameter = DatafileParameter.objects.get(pk=parameter_id)
    dataset_file = parameter.parameterset.dataset_file
    experiment_id = dataset_file.dataset.experiment.id
    if authz.has_datafile_access(request, dataset_file.id):
        return load_image(request, experiment_id, parameter)
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
    request, dataset_file_id, parameterset_id, parameter_name):

    # TODO handle not exist

    if not authz.has_datafile_access(request, dataset_file_id):
        return return_response_error(request)

    image = DatafileParameter.objects.get(name__name=parameter_name,
                                          parameterset=parameterset_id)

    return HttpResponse(b64decode(image.string_value), mimetype='image/jpeg')


def about(request):

    c = Context({'subtitle': 'About',
                 'about_pressed': True,
                 'nav': [{'name': 'About', 'link': '/about/'}]})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/about.html', c))


def partners(request):

    c = Context({})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/partners.html', c))


def experiment_index(request):

    experiments = None

    if request.user.is_authenticated():
        experiments = authz.get_accessible_experiments(request)
        if experiments:
            experiments = experiments.order_by('-update_time')

    public_experiments = Experiment.objects.filter(public=True)
    if public_experiments:
        public_experiments = public_experiments.order_by('-update_time')

    c = Context({
        'experiments': experiments,
        'public_experiments': public_experiments,
        'subtitle': 'Experiment Index',
        'bodyclass': 'list',
        'nav': [{'name': 'Data', 'link': '/experiment/view/'}],
        'next': '/experiment/view/',
        'data_pressed': True})

    return HttpResponse(render_response_search(request,
                        'tardis_portal/experiment_index.html', c))


@authz.experiment_access_required
def view_experiment(request, experiment_id):
    """View an existing experiment.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param experiment_id: the ID of the experiment to be edited
    :type experiment_id: string
    :rtype: :class:`django.http.HttpResponse`

    """
    c = Context({})

    try:
        experiment = Experiment.safe.get(request, experiment_id)
    except PermissionDenied:
        return return_response_error(request)
    except Experiment.DoesNotExist:
        return return_response_not_found(request)

    c['experiment'] = experiment
    c['has_write_permissions'] = \
        authz.has_write_permissions(request, experiment_id)
    c['subtitle'] = experiment.title
    c['nav'] = [{'name': 'Data', 'link': '/experiment/view/'},
                {'name': experiment.title,
                 'link': experiment.get_absolute_url()}]

    if 'status' in request.GET:
        c['status'] = request.GET['status']
    if 'error' in request.GET:
        c['error'] = request.GET['error']

    return HttpResponse(render_response_index(request,
                        'tardis_portal/view_experiment.html', c))


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
        experiment = Experiment.safe.get(request, experiment_id)
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
        Dataset_File.objects.filter(dataset__experiment=experiment_id)

    acl = ExperimentACL.objects.filter(pluginId=django_user,
                                       experiment=experiment,
                                       isOwner=True)

    # TODO: resolve usernames through UserProvider!
    c['owners'] = [User.objects.get(pk=str(a.entityId)) for a in acl]

    # calculate the sum of the datafile sizes
    size = 0
    for df in c['datafiles']:
        try:
            size = size + long(df.size)
        except:
            pass
    c['size'] = size

    c['has_write_permissions'] = \
        authz.has_write_permissions(request, experiment_id)

    c['protocol'] = []
    download_urls = experiment.get_download_urls()
    for key, value in download_urls.iteritems():
        c['protocol'] += [[key, value]]

    if 'status' in request.GET:
        c['status'] = request.GET['status']
    if 'error' in request.GET:
        c['error'] = request.GET['error']

    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/experiment_description.html', c))


@authz.experiment_access_required
def experiment_datasets(request, experiment_id):
    """View a listing of dataset of an existing experiment as ajax loaded tab.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param experiment_id: the ID of the experiment to be edited
    :type experiment_id: string
    :param template_name: the path of the template to render
    :type template_name: string
    :rtype: :class:`django.http.HttpResponse`

    """
    c = Context({'upload_complete_url':
                     reverse('tardis.tardis_portal.views.upload_complete'),
                 'searchDatafileSelectionForm':
                     getNewSearchDatafileSelectionForm(),
                 })

    try:
        experiment = Experiment.safe.get(request, experiment_id)
    except PermissionDenied:
        return return_response_error(request)
    except Experiment.DoesNotExist:
        return return_response_not_found(request)

    c['experiment'] = experiment
    c['datafiles'] = \
        Dataset_File.objects.filter(dataset__experiment=experiment_id)

    c['has_write_permissions'] = \
        authz.has_write_permissions(request, experiment_id)

    c['protocol'] = []
    download_urls = experiment.get_download_urls()
    for key, value in download_urls.iteritems():
        c['protocol'] += [[key, value]]

    if 'status' in request.GET:
        c['status'] = request.GET['status']
    if 'error' in request.GET:
        c['error'] = request.GET['error']

    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/experiment_datasets.html', c))


@authz.dataset_access_required
def retrieve_dataset_metadata(request, dataset_id):
    dataset = Dataset.objects.get(pk=dataset_id)
    c = Context({'dataset': dataset, })
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/dataset_metadata.html', c))


@authz.experiment_access_required
def retrieve_experiment_metadata(request, experiment_id):
    experiment = Experiment.objects.get(pk=experiment_id)
    c = Context({'experiment': experiment, })
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/experiment_metadata.html', c))


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
        'directory_listing': staging_traverse(),
        'user_id': request.user.id,
        })

    if request.method == 'POST':
        form = ExperimentForm(request.POST, request.FILES)
        if form.is_valid():
            full_experiment = form.save(commit=False)

            # group/owner assignment stuff, soon to be replaced

            experiment = full_experiment['experiment']
            experiment.created_by = request.user
            for df in full_experiment['dataset_files']:
                if not df.url.startswith(path.sep):
                    df.url = path.join(settings.STAGING_PATH,
                                       df.url)
            full_experiment.save_m2m()

            # add defaul ACL
            acl = ExperimentACL(experiment=experiment,
                                pluginId=django_user,
                                entityId=str(request.user.id),
                                canRead=True,
                                canWrite=True,
                                canDelete=True,
                                isOwner=True,
                                aclOwnershipType=ExperimentACL.OWNER_OWNED)
            acl.save()

            params = urlencode({'status': "Experiment Saved."})
            return HttpResponseRedirect(
                '?'.join([experiment.get_absolute_url(), params]))

        c['status'] = "Errors exist in form."
        c["error"] = 'true'

    else:
        form = ExperimentForm(extra=1)

    c['form'] = form
    return HttpResponse(render_response_index(request, template_name, c))


@authz.experiment_access_required
def metsexport_experiment(request, experiment_id):

    from os.path import basename
    from django.core.servers.basehttp import FileWrapper
    from tardis.tardis_portal.metsexporter import exporter
    filename = exporter.export(experiment_id)
    response = HttpResponse(FileWrapper(file(filename)),
                            mimetype='application')
    response['Content-Disposition'] = \
        'attachment; filename="%s"' % basename(filename)
    return response


@login_required
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
                 'user_id': request.user.id,
              })

    if request.method == 'POST':
        form = ExperimentForm(request.POST, request.FILES,
                              instance=experiment, extra=0)
        if form.is_valid():
            full_experiment = form.save(commit=False)

            experiment = full_experiment['experiment']
            experiment.created_by = request.user
            for df in full_experiment['dataset_files']:
                if not df.url.startswith(path.sep):
                    df.url = path.join(settings.STAGING_PATH, df.url)
            full_experiment.save_m2m()

            params = urlencode({'status': "Experiment Saved."})
            return HttpResponseRedirect(
                '?'.join([experiment.get_absolute_url(),
                          params]))

        c['status'] = "Errors exist in form."
        c["error"] = 'true'
    else:
        form = ExperimentForm(instance=experiment, extra=0)

    c['directory_listing'] = staging_traverse()
    c['form'] = form

    return HttpResponse(render_response_index(request,
                        template, c))


# todo complete....
def login(request):
    from tardis.tardis_portal.auth import login, auth_service

    if type(request.user) is not AnonymousUser:
        # redirect the user to the home page if he is trying to go to the
        # login page
        return HttpResponseRedirect('/')

    # TODO: put me in SETTINGS
    if 'username' in request.POST and \
            'password' in request.POST:
        authMethod = request.POST['authMethod']

        if 'next' not in request.GET:
            next = '/'
        else:
            next = request.GET['next']

        user = auth_service.authenticate(
            authMethod=authMethod, request=request)

        if user:
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return HttpResponseRedirect(next)

        c = Context({'status': "Sorry, username and password don't match.",
                     'error': True,
                     'loginForm': LoginForm()})
        return return_response_error_message(
            request, 'tardis_portal/login.html', c)

    c = Context({'loginForm': LoginForm()})

    return HttpResponse(render_response_index(request,
                        'tardis_portal/login.html', c))


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


def register_experiment_ws_xmldata_internal(request):
    logger.debug('def register_experiment_ws_xmldata_internal')
    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']
        filename = request.POST['filename']
        eid = request.POST['eid']

        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        if user is not None:
            if not user.is_active:
                return return_response_error(request)
        else:
            return return_response_error(request)

        _registerExperimentDocument(filename=filename,
                created_by=user, expid=eid)

        response = HttpResponse('Finished cataloging: %s' % eid,
                                status=200)
        response['Location'] = request.build_absolute_uri(
            '/experiment/view/' + str(eid))

        return response


# TODO removed username from arguments
def _registerExperimentDocument(filename, created_by, expid=None,
                                owners=[], username=None):
    '''
    Register the experiment document and return the experiment id.

    :param filename: path of the document to parse (METS or notMETS)
    :type filename: string
    :param created_by: a User instance
    :type created_by: :py:class:`django.contrib.auth.models.User`
    :param expid: the experiment ID to use
    :type expid: int
    :param owners: a list of owners
    :type owner: list
    :param username: **UNUSED**
    :rtype: int

    '''

    f = open(filename)
    firstline = f.readline()
    f.close()

    if firstline.startswith('<experiment'):
        logger.debug('processing simple xml')
        processExperiment = ProcessExperiment()
        eid = processExperiment.process_simple(filename, created_by, expid)

    else:
        logger.debug('processing METS')
        eid = parseMets(filename, created_by, expid)

    # for each PI
    for owner in owners:
        if owner:
            # TODO: enable LDAP module here!

            # try get user from email
            # if settings.LDAP_ENABLE:
            #     u = ldap_auth.get_or_create_user_ldap(owner)
            # else:
                # print "owner", owner
            u = User.objects.get(username=owner)

            # if exist, create ACL
            if u:
                logger.debug('registering owner: ' + owner)
                e = Experiment.objects.get(pk=eid)

                acl = ExperimentACL(experiment=e,
                                    pluginId=django_user,
                                    entityId=str(u.id),
                                    canRead=True,
                                    canWrite=True,
                                    canDelete=True,
                                    isOwner=True,
                                    aclOwnershipType=ExperimentACL.OWNER_OWNED)
                acl.save()

    return eid


# web service
def register_experiment_ws_xmldata(request):
    import threading

    status = ''
    if request.method == 'POST':  # If the form has been submitted...

        # A form bound to the POST data
        form = RegisterExperimentForm(request.POST, request.FILES)
        if form.is_valid():  # All validation rules pass

            xmldata = request.FILES['xmldata']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            originid = form.cleaned_data['originid']

            from_url = None
            if 'form_url' in request.POST:
                from_url = request.POST['from_url']

            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    return return_response_error(request)
            else:
                return return_response_error(request)

            e = Experiment(
                title='Placeholder Title',
                approved=True,
                created_by=user,
                )
            e.save()

            eid = e.id

            # TODO: this entire function needs a fancy class with functions for
            # each part..
            from os import makedirs, system
            from os.path import exists, join
            dir = join(settings.FILE_STORE_PATH, str(eid))
            if not exists(dir):
                makedirs(dir)
                system('chmod g+w ' + dir)

            filename = dir + '/METS.xml'
            file = open(filename, 'wb+')
            for chunk in xmldata.chunks():
                file.write(chunk)
            file.close()

            class RegisterThread(threading.Thread):

                @transaction.commit_on_success
                def run(self):
                    logger.info('=== processing experiment %s: START' % eid)
                    owners = request.POST.getlist('experiment_owner')
                    try:
                        _registerExperimentDocument(filename=filename,
                                                    created_by=user,
                                                    expid=eid,
                                                    owners=owners,
                                                    username=username)
                        logger.info('=== processing experiment %s: DONE' % eid)
                    except:
                        e.delete()
                        logger.exception('=== processing experiment %s: FAILED!' % eid)
            RegisterThread().start()

            if from_url:

                class FileTransferThread(threading.Thread):

                    def run(self):
                        # todo remove hard coded u/p for sync transfer....
                        logger.debug('started transfer thread')
                        file_transfer_url = from_url + '/file_transfer/'
                        data = urlencode({
                            'originid': str(originid),
                            'eid': str(eid),
                            'site_settings_url': request.build_absolute_uri(
                                    '/site-settings.xml/'),
                            'username': str('synchrotron'),
                            'password': str('tardis'),
                            })
                        urlopen(file_transfer_url, data)

                logger.debug('Sending file request')
                FileTransferThread().start()

            logger.debug('returning response from main call')
            response = HttpResponse(str(eid), status=200)
            response['Location'] = request.build_absolute_uri(
                '/experiment/view/' + str(eid))
            return response
    else:
        form = RegisterExperimentForm()  # An unbound form

    c = Context({
        'form': form,
        'status': status,
        'subtitle': 'Register Experiment',
        'searchDatafileSelectionForm': getNewSearchDatafileSelectionForm()})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/register_experiment.html', c))


@authz.datafile_access_required
def retrieve_parameters(request, dataset_file_id):

    parametersets = DatafileParameterSet.objects.all()
    parametersets = parametersets.filter(dataset_file__pk=dataset_file_id)

    c = Context({'parametersets': parametersets})

    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/parameters.html', c))


@authz.dataset_access_required
def retrieve_datafile_list(request, dataset_id):

    dataset_results = \
        Dataset_File.objects.filter(
        dataset__pk=dataset_id).order_by('filename')

    filename_search = None

    if 'filename' in request.GET and len(request.GET['filename']):
        filename_search = request.GET['filename']
        dataset_results = \
            dataset_results.filter(url__icontains=filename_search)

    # pagination was removed by someone in the interface but not here.
    # need to fix.
    pgresults = 10000
    # if request.mobile:
    #     pgresults = 30
    # else:
    #     pgresults = 25

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

    if request.user.is_authenticated():
        experiment_id = Experiment.objects.get(dataset__id=dataset_id).id
        is_owner = authz.has_experiment_ownership(request, experiment_id)

    c = Context({
        'dataset': dataset,
        'paginator': paginator,
        'dataset_id': dataset_id,
        'filename_search': filename_search,
        'is_owner': is_owner,
        })
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/datafile_list.html', c))


@login_required()
def control_panel(request):

    experiments = Experiment.safe.owned(request)
    if experiments:
        experiments = experiments.order_by('title')

    c = Context({'experiments': experiments,
                 'subtitle': 'Experiment Control Panel'})

    return HttpResponse(render_response_index(request,
                        'tardis_portal/control_panel.html', c))


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

    c = Context({'header': 'Search Experiment',
                 'experiments': experiments,
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
    logger.info('__getFilteredDatafiles: searchFilterData {0}'.format(searchFilterData))

    # there's no need to do any filtering if we didn't find any
    # datafiles that the user has access to
    if not datafile_results:
        logger.info("""__getFilteredDatafiles: user {0} doesn\'t have
                    access to any experiments""".format(request.user))
        return datafile_results

    datafile_results = \
        datafile_results.filter(
datafileparameterset__datafileparameter__name__schema__namespace__in=Schema.getNamespaces(
        Schema.DATAFILE, searchQueryType)).distinct()

    # if filename is searchable which i think will always be the case...
    if searchFilterData['filename'] != '':
        datafile_results = \
            datafile_results.filter(
            filename__icontains=searchFilterData['filename'])
    # TODO: might need to cache the result of this later on

    # get all the datafile parameters for the given schema
    parameters = [p for p in
        ParameterName.objects.filter(
        schema__namespace__in=Schema.getNamespaces(Schema.DATAFILE,
        searchQueryType))]

    datafile_results = __filterParameters(parameters, datafile_results,
            searchFilterData, 'datafileparameterset__datafileparameter')

    # get all the dataset parameters for given schema
    parameters = [p for p in
        ParameterName.objects.filter(
        schema__namespace__in=Schema.getNamespaces(Schema.DATASET,
        searchQueryType))]

    datafile_results = __filterParameters(parameters, datafile_results,
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
        experiments = \
            experiments.filter(
            institution_name__icontains=searchFilterData['institutionName'])

    if searchFilterData['creator'] != '':
        experiments = \
            experiments.filter(
            author_experiment__author__icontains=searchFilterData['creator'])

    date = searchFilterData['date']
    if not date == None:
        experiments = \
            experiments.filter(start_time__lt=date, end_time__gt=date)

    # initialise the extra experiment parameters
    parameters = []

    # get all the experiment parameters
    for experimentSchema in Schema.getNamespaces(Schema.EXPERIMENT):
        parameters += ParameterName.objects.filter(
            schema__namespace__exact=experimentSchema)

    experiments = __filterParameters(parameters, experiments,
            searchFilterData, 'experimentparameterset__experimentparameter')

    # let's sort it in the end
    if experiments:
        experiments = experiments.order_by('title')

    return experiments


def __filterParameters(parameters, datafile_results,
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
       :py:class:`tardis.tardis_portal.models.Dataset_File`

    :returns: A list of datafiles as a result of the query or None if the
      provided search request is invalid

    """

    for parameter in parameters:
        kwargs = {paramType + '__name__name__icontains': parameter.name}
        try:

            # if parameter is a string...
            if not parameter.data_type == ParameterName.NUMERIC:
                if searchFilterData[parameter.name] != '':
                    # let's check if this is a field that's specified to be
                    # displayed as a dropdown menu in the form
                    if parameter.choices != '':
                        if searchFilterData[parameter.name] != '-':
                            kwargs[paramType + '__string_value__iexact'] = \
                                searchFilterData[parameter.name]
                    else:
                        if parameter.comparison_type == \
                                ParameterName.EXACT_VALUE_COMPARISON:
                            kwargs[paramType + '__string_value__iexact'] = \
                                searchFilterData[parameter.name]
                        elif parameter.comparison_type == \
                                ParameterName.CONTAINS_COMPARISON:
                            # we'll implement exact comparison as 'icontains'
                            # for now
                            kwargs[paramType + '__string_value__icontains'] = \
                                searchFilterData[parameter.name]
                        else:
                            # if comparison_type on a string is a comparison
                            # type that can only be applied to a numeric value,
                            # we'll default to just using 'icontains'
                            # comparison
                            kwargs[paramType + '__string_value__icontains'] = \
                                searchFilterData[parameter.name]
                else:
                    pass
            else:  # parameter.isNumeric():
                if parameter.comparison_type == \
                        ParameterName.RANGE_COMPARISON:
                    fromParam = searchFilterData[parameter.name + 'From']
                    toParam = searchFilterData[parameter.name + 'To']
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

                elif searchFilterData[parameter.name] is not None:

                    # if parameter is an number and we want to handle other
                    # type of number comparisons
                    if parameter.comparison_type == \
                            ParameterName.EXACT_VALUE_COMPARISON:
                        kwargs[paramType + '__numerical_value__exact'] = \
                            searchFilterData[parameter.name]

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
                            searchFilterData[parameter.name]
                    elif parameter.comparison_type == \
                            ParameterName.GREATER_THAN_EQUAL_COMPARISON:
                        kwargs[paramType + '__numerical_value__gte'] = \
                            searchFilterData[parameter.name]
                    elif parameter.comparison_type == \
                            ParameterName.LESS_THAN_COMPARISON:
                        kwargs[paramType + '__numerical_value__lt'] = \
                            searchFilterData[parameter.name]
                    elif parameter.comparison_type == \
                            ParameterName.LESS_THAN_EQUAL_COMPARISON:
                        kwargs[paramType + '__numerical_value__lte'] = \
                            searchFilterData[parameter.name]
                    else:
                        # if comparison_type on a numeric is a comparison type
                        # that can only be applied to a string value, we'll
                        # default to just using 'exact' comparison
                        kwargs[paramType + '__numerical_value__exact'] = \
                            searchFilterData[parameter.name]
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

    url = 'tardis_portal/search_datafile_form.html'
    if not searchForm:
        #if searchQueryType == 'saxs':
        SearchDatafileForm = createSearchDatafileForm(searchQueryType)
        searchForm = SearchDatafileForm()
        #else:
        #    # TODO: what do we need to do if the user didn't provide a page to
        #            display?
        #    pass

    # TODO: remove this later on when we have a more generic search form
    if searchQueryType == 'mx':
        url = 'tardis_portal/search_datafile_form_mx.html'

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
    :rtype: list of :py:class:`tardis.tardis_portal.models.Dataset_Files` or
       None

    """

    if form.is_valid():

        datafile_results = __getFilteredDatafiles(request,
            searchQueryType, form.cleaned_data)

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


def search_datafile(request):
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
                datafile_results = __processDatafileParameters(request,
                    searchQueryType, form)
                if datafile_results is not None:
                    bodyclass = 'list'
                else:
                    return __forwardToSearchDatafileFormPage(request,
                        searchQueryType, form)
        else:
            # display the form
            if 'datafileResults' in request.session:
                del request.session['datafileResults']
            return __forwardToSearchDatafileFormPage(request, searchQueryType)

    # process the files to be displayed by the paginator...
    paginator = Paginator(datafile_results,
                          constants.DATAFILE_RESULTS_PER_PAGE)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of :range, deliver last page of results.
    try:
        datafiles = paginator.page(page)
    except (EmptyPage, InvalidPage):
        datafiles = paginator.page(paginator.num_pages)

    import re
    cleanedUpQueryString = re.sub('&page=\d+', '',
        request.META['QUERY_STRING'])

    c = Context({
        'datafiles': datafiles,
        'paginator': paginator,
        'query_string': cleanedUpQueryString,
        'subtitle': 'Search Datafiles',
        'nav': [{'name': 'Search Datafile', 'link': '/search/datafile/'}],
        'bodyclass': bodyclass,
        'search_pressed': True,
        'searchDatafileSelectionForm': getNewSearchDatafileSelectionForm()})
    url = 'tardis_portal/search_datafile_results.html'
    return HttpResponse(render_response_index(request, url, c))


@login_required()
def retrieve_user_list(request):
    authMethod = request.GET['authMethod']

    if authMethod == localdb_auth_key:
        users = [userProfile.user for userProfile in
                 UserProfile.objects.filter(isDjangoAccount=True)]
        users = sorted(users, key=lambda user: user.username)
    else:
        users = [userAuth for userAuth in
                 UserAuthentication.objects.filter(
                     authenticationMethod=authMethod)
                 if userAuth.userProfile.isDjangoAccount == False]
        if users:
            users = sorted(users, key=lambda userAuth: userAuth.username)
        else:
            users = User.objects.none()
    # print users
    userlist = ' '.join([str(u) for u in users])
    return HttpResponse(userlist)


@login_required()
def retrieve_group_list(request):

    grouplist = ' ~ '.join(map(str, Group.objects.all().order_by('name')))
    return HttpResponse(grouplist)


@authz.experiment_ownership_required
def retrieve_access_list_user(request, experiment_id):

    from tardis.tardis_portal.forms import AddUserPermissionsForm
    users = Experiment.safe.users(request, experiment_id)

    c = Context({'users': users, 'experiment_id': experiment_id,
                 'addUserPermissionsForm': AddUserPermissionsForm()})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/access_list_user.html', c))


@authz.experiment_ownership_required
def retrieve_access_list_group(request, experiment_id):

    from tardis.tardis_portal.forms import AddGroupPermissionsForm

    user_owned_groups = Experiment.safe.user_owned_groups(request,
                                                          experiment_id)
    system_owned_groups = Experiment.safe.system_owned_groups(request,
                                                            experiment_id)

    c = Context({'user_owned_groups': user_owned_groups,
                 'system_owned_groups': system_owned_groups,
                 'experiment_id': experiment_id,
                 'addGroupPermissionsForm': AddGroupPermissionsForm()})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/access_list_group.html', c))


@authz.experiment_ownership_required
def retrieve_access_list_external(request, experiment_id):

    groups = Experiment.safe.external_users(request, experiment_id)
    c = Context({'groups': groups, 'experiment_id': experiment_id})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/access_list_external.html', c))


@authz.group_ownership_required
def retrieve_group_userlist(request, group_id):

    from tardis.tardis_portal.forms import ManageGroupPermissionsForm
    users = User.objects.filter(groups__id=group_id)
    c = Context({'users': users, 'group_id': group_id,
                 'manageGroupPermissionsForm': ManageGroupPermissionsForm()})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/group_user_list.html', c))


@login_required()
def manage_groups(request):

    groups = Group.objects.filter(groupadmin__user=request.user)
    c = Context({'groups': groups})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/manage_group_members.html', c))


@authz.group_ownership_required
def add_user_to_group(request, group_id, username):

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
            user = UserAuthentication.objects.get(username=username,
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
    return HttpResponse(render_response_index(request,
         'tardis_portal/ajax/add_user_to_group_result.html', c))


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


@transaction.commit_on_success
@authz.experiment_ownership_required
def add_experiment_access_user(request, experiment_id, username):

    canRead = False
    canWrite = False
    canDelete = False

    if 'canRead' in request.GET:
        if request.GET['canRead'] == 'true':
            canRead = True

    if 'canWrite' in request.GET:
        if request.GET['canWrite'] == 'true':
            canWrite = True

    if 'canDelete' in request.GET:
        if request.GET['canDelete'] == 'true':
            canDelete = True

    try:
        authMethod = request.GET['authMethod']
        if authMethod == localdb_auth_key:
            user = User.objects.get(username=username)
        else:
            user = UserAuthentication.objects.get(username=username,
                authenticationMethod=authMethod).userProfile.user
    except User.DoesNotExist:
        return HttpResponse('User %s does not exist.' % (username))
    except UserAuthentication.DoesNotExist:
        return HttpResponse('User %s does not exist' % (username))

    try:
        experiment = Experiment.objects.get(pk=experiment_id)
    except Experiment.DoesNotExist:
        return HttpResponse('Experiment (id=%d) does not exist.' % (experiment.id))

    acl = ExperimentACL.objects.filter(
        experiment=experiment,
        pluginId=django_user,
        entityId=str(user.id),
        aclOwnershipType=ExperimentACL.OWNER_OWNED)

    if acl.count() == 0:
        acl = ExperimentACL(experiment=experiment,
                            pluginId=django_user,
                            entityId=str(user.id),
                            canRead=canRead,
                            canWrite=canWrite,
                            canDelete=canDelete,
                            aclOwnershipType=ExperimentACL.OWNER_OWNED)

        acl.save()
        c = Context({'authMethod': authMethod,
                     'user': user,
                     'username': username,
                     'experiment_id': experiment_id})

        return HttpResponse(render_response_index(request,
            'tardis_portal/ajax/add_user_result.html', c))

    return HttpResponse('User already has experiment access.')


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

    acl = ExperimentACL.objects.filter(
        experiment=experiment,
        pluginId=django_user,
        entityId=str(user.id),
        aclOwnershipType=ExperimentACL.OWNER_OWNED)

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
        acl = ExperimentACL.objects.get(
            experiment=experiment,
            pluginId=django_user,
            entityId=str(user.id),
            aclOwnershipType=ExperimentACL.OWNER_OWNED)
    except ExperimentACL.DoesNotExist:
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

    return HttpResponse(render_response_index(request,
                            'tardis_portal/form_template.html', c))


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
        acl = ExperimentACL.objects.get(
            experiment=experiment,
            pluginId=django_group,
            entityId=str(group.id),
            aclOwnershipType=ExperimentACL.OWNER_OWNED)
    except ExperimentACL.DoesNotExist:
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

    return HttpResponse(render_response_index(request,
                            'tardis_portal/form_template.html', c))


@authz.experiment_ownership_required
def add_experiment_access_group(request, experiment_id, groupname):

    create = False
    canRead = False
    canWrite = False
    canDelete = False
    authMethod = localdb_auth_key
    admin = None

    if 'canRead' in request.GET:
        if request.GET['canRead'] == 'true':
            canRead = True

    if 'canWrite' in request.GET:
        if request.GET['canWrite'] == 'true':
            canWrite = True

    if 'canDelete' in request.GET:
        if request.GET['canDelete'] == 'true':
            canDelete = True

    if 'admin' in request.GET:
        admin = request.GET['admin']

    if 'create' in request.GET:
        if request.GET['create'] == 'true':
            create = True

    try:
        experiment = Experiment.objects.get(pk=experiment_id)
    except Experiment.DoesNotExist:
        return HttpResponse('Experiment (id=%d) does not exist' % (experiment_id))

    # TODO: enable transaction management here...
    if create:
        try:
            group = Group(name=groupname)
            group.save()
        except:
            return HttpResponse('Could not create group %s ' \
            '(It is likely that it already exists)' % (groupname))
    else:
        try:
            group = Group.objects.get(name=groupname)
        except Group.DoesNotExist:
            return HttpResponse('Group %s does not exist' % (groupname))

    acl = ExperimentACL.objects.filter(
        experiment=experiment,
        pluginId=django_group,
        entityId=str(group.id),
        aclOwnershipType=ExperimentACL.OWNER_OWNED)

    if acl.count() > 0:
        # an acl role already exists
        # todo: not sure why this was the only error condition
        # that returns an error
        return return_response_error(request)

    acl = ExperimentACL(experiment=experiment,
                        pluginId=django_group,
                        entityId=str(group.id),
                        canRead=canRead,
                        canWrite=canWrite,
                        canDelete=canDelete,
                        aclOwnershipType=ExperimentACL.OWNER_OWNED)
    acl.save()

    # todo if the admin specified doesnt exist then the 'add group + add user'
    # workflow bails halfway through. This seems to add a group which wont be
    # displayed in the manage groups view but does appear in the admin
    # page. Is this the desired behaviour?
    adminuser = None
    if admin:
        try:
            authMethod = request.GET['authMethod']
            if authMethod == localdb_auth_key:
                adminuser = User.objects.get(username=admin)
            else:
                adminuser = UserAuthentication.objects.get(username=admin,
                    authenticationMethod=authMethod).userProfile.user

        except User.DoesNotExist:
            return HttpResponse('User %s does not exist' % (admin))
        except UserAuthentication.DoesNotExist:
            return HttpResponse('User %s does not exist' % (admin))
        except UserAuthentication.DoesNotExist:
            return return_response_error(request)

        # create admin for this group and add it to the group
        groupadmin = GroupAdmin(user=adminuser, group=group)
        groupadmin.save()

        adminuser.groups.add(group)
        adminuser.save()

    # add the current user as admin as well for newly created groups
    if create and not request.user == adminuser:
        user = request.user

        groupadmin = GroupAdmin(user=user, group=group)
        groupadmin.save()

        user.groups.add(group)
        user.save()

    c = Context({'group': group,
                 'experiment_id': experiment_id})

    return HttpResponse(render_response_index(request,
        'tardis_portal/ajax/add_group_result.html', c))


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

    acl = ExperimentACL.objects.filter(
        experiment=experiment,
        pluginId=django_group,
        entityId=str(group.id),
        aclOwnershipType=ExperimentACL.OWNER_OWNED)

    if acl.count() == 1:
        acl[0].delete()
        return HttpResponse('OK')
    elif acl.count() == 0:
        return HttpResponse('No ACL available.'
                            'It is likely the group doesnt have access to this experiment.')
    else:
        return HttpResponse('Multiple ACLs found')

    return HttpResponse('')


@authz.experiment_ownership_required
def publish_experiment(request, experiment_id):

    experiment = Experiment.objects.get(id=experiment_id)

    if not experiment.public:
        filename = settings.FILE_STORE_PATH + '/' + experiment_id + \
            '/METS.XML'

        mpform = MultiPartForm()
        mpform.add_field('username', settings.TARDIS_USERNAME)
        mpform.add_field('password', settings.TARDIS_PASSWORD)
        mpform.add_field('url', request.build_absolute_uri('/'))
        mpform.add_field('mytardis_id', experiment_id)

        f = open(filename, 'r')

        # Add a fake file

        mpform.add_file('xmldata', 'METS.xml', fileHandle=f)

        logger.debug('about to send register request to site')

        # Build the request

        requestmp = urllib2.Request(settings.TARDIS_REGISTER_URL)
        requestmp.add_header('User-agent',
                             'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
        body = str(mpform)
        requestmp.add_header('Content-type', mpform.get_content_type())
        requestmp.add_header('Content-length', len(body))
        requestmp.add_data(body)

        logger.debug('OUTGOING DATA:')
        logger.debug(requestmp.get_data())

        logger.debug('SERVER RESPONSE:')
        logger.debug(urllib2.urlopen(requestmp).read())

        experiment.public = True
        experiment.save()

        c = Context({})
        return HttpResponse(render_response_index(request,
                            'tardis_portal/index.html', c))
    else:
        return return_response_error(request)


def stats(request):

    # stats

    public_datafiles = Dataset_File.objects.filter()
    public_experiments = Experiment.objects.filter()

    size = 0
    for df in public_datafiles:
        try:
            size = size + long(df.size)
        except:
            pass

    public_datafile_size = size

    # using count() is more efficient than using len() on a query set
    c = Context({'public_datafiles': public_datafiles.count(),
                'public_experiments': public_experiments.count(),
                'public_datafile_size': public_datafile_size})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/stats.html', c))


def import_params(request):
    if request.method == 'POST':  # If the form has been submitted...

        # A form bound to the POST data
        form = ImportParamsForm(request.POST, request.FILES)
        if form.is_valid():  # All validation rules pass

            params = request.FILES['params']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            if user is not None:
                if not user.is_active or not user.is_staff:
                    return return_response_error(request)
            else:
                return return_response_error(request)

            i = 0
            for line in params:
                if i == 0:
                    prefix = line
                    logger.debug(prefix)
                elif i == 1:
                    schema = line
                    logger.debug(schema)

                    try:
                        Schema.objects.get(namespace=schema)
                        return HttpResponse('Schema already exists.')
                    except Schema.DoesNotExist:
                        schema_db = Schema(namespace=schema)
                        # TODO: add the extra info that the Schema instance
                        #       needs
                        schema_db.save()
                else:
                    part = line.split('^')
                    if len(part) == 4:

                        is_numeric = False
                        if part[3].strip(' \n\r') == 'True':
                            is_numeric = True
                        if is_numeric:
                            pn = ParameterName(schema=schema_db,
                                               name=part[0], full_name=part[1],
                                               units=part[2],
                                               data_type=ParameterName.NUMERIC)
                        else:

                            pn = ParameterName(schema=schema_db,
                                               name=part[0], full_name=part[1],
                                               units=part[2],
                                               data_type=ParameterName.STRING)
                        pn.save()

                i = i + 1

            return HttpResponse('OK')
    else:
        form = ImportParamsForm()

    c = Context({'form': form, 'header': 'Import Parameters'})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/form_template.html', c))


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


def upload(request, dataset_id, *args, **kwargs):
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

            #print 'about to write uploaded file'
            filepath = write_uploaded_file_to_dataset(dataset,
                    uploaded_file_post)
            #print filepath

            add_datafile_to_dataset(dataset, filepath,
                                    uploaded_file_post.size)
            #print 'added datafile to dataset'

    return HttpResponse('True')


def upload_files(request, dataset_id,
                 template_name='tardis_portal/ajax/upload_files.html'):
    """
    Creates an Uploadify 'create files' button with a dataset
    destination. `A workaround for a JQuery Dialog conflict\
    <http://www.uploadify.com/forums/discussion/3348/uploadify-in-jquery-ui-dialog-modal-causes-double-queue-item/p1>`_

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param template_name: the path of the template to render
    :param dataset_id: the dataset_id
    :type dataset_id: integer
    :returns: A view containing an Uploadify *create files* button
    """
    url = reverse('tardis.tardis_portal.views.upload_complete')
    c = Context({'upload_complete_url': url, 'dataset_id': dataset_id})
    return render_to_response(template_name, c)


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
    if authz.has_write_permissions(request, parameterset.dataset.experiment.id):
        return edit_parameters(request, parameterset, otype="dataset")
    else:
        return return_response_error(request)


@login_required
def edit_datafile_par(request, parameterset_id):
    parameterset = DatafileParameterSet.objects.get(id=parameterset_id)
    if authz.has_write_permissions(request, parameterset.datafile.dataset.experiment.id):
        return edit_parameters(request, parameterset, otype="datafile")
    else:
        return return_response_error(request)


def edit_parameters(request, parameterset, otype):

    parameternames = ParameterName.objects.filter(
        schema__namespace=parameterset.schema.namespace)
    success = False
    valid = True

    if request.method == 'POST':

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
        'schema': parameterset.schema.namespace,
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
    parentObject = Dataset_File.objects.get(id=datafile_id)
    if authz.has_write_permissions(request, parentObject.dataset.experiment.id):
        return add_par(request, parentObject, otype="datafile")
    else:
        return return_response_error(request)


@login_required
def add_dataset_par(request, dataset_id):
    parentObject = Dataset.objects.get(id=dataset_id)
    if authz.has_write_permissions(request, parentObject.experiment.id):
        return add_par(request, parentObject, otype="dataset")
    else:
        return return_response_error(request)


@login_required
def add_experiment_par(request, experiment_id):
    parentObject = Experiment.objects.get(id=experiment_id)
    if authz.has_write_permissions(request, parentObject.id):
        return add_par(request, parentObject, otype="experiment")
    else:
        return return_response_error(request)


def add_par(request, parentObject, otype):

    all_schema = Schema.objects.all()

    if 'schema_id' in request.GET:
        schema_id = request.GET['schema_id']
    else:
        schema_id = all_schema[0].id

    schema = Schema.objects.get(id=schema_id)

    parameternames = ParameterName.objects.filter(
        schema__namespace=schema.namespace)

    success = False
    valid = True

    if request.method == 'POST':

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
