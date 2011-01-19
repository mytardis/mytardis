#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
views.py

.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>
.. moduleauthor::  Gerson Galang <gerson.galang@versi.edu.au>

"""

import shutil
from base64 import b64decode

from django.template import Context, loader
from django.http import HttpResponse

from django.conf import settings

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.http import HttpResponseRedirect, HttpResponseForbidden, \
    HttpResponseNotFound, HttpResponseServerError
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from tardis.tardis_portal import ProcessExperiment
from tardis.tardis_portal.forms import *
from tardis.tardis_portal.errors import *
from tardis.tardis_portal.logger import logger

from django.core.paginator import Paginator, InvalidPage, EmptyPage

from tardis.tardis_portal.models import *
from tardis.tardis_portal import constants

import urllib
import urllib2
import datetime

import os
from os import path

from tardis.tardis_portal import ldap_auth

from tardis.tardis_portal.MultiPartForm import MultiPartForm

from tardis.tardis_portal.metsparser import parseMets

from django.db import transaction


def getNewSearchDatafileSelectionForm():
    DatafileSelectionForm = createSearchDatafileSelectionForm()
    return DatafileSelectionForm()


def render_response_index(request, *args, **kwargs):

    kwargs['context_instance'] = RequestContext(request)

    kwargs['context_instance']['is_authenticated'] = \
        request.user.is_authenticated()
    kwargs['context_instance']['username'] = request.user.username

    if request.mobile:
        template_path = args[0]
        split = template_path.partition('/')
        args = (split[0] + '/mobile/' + split[2], ) + args[1:]

    return render_to_response(*args, **kwargs)


def return_response_error(request):
    c = Context({'status': 'ERROR: Forbidden', 'error': True})
    return HttpResponseForbidden(render_response_index(request,
                                 'tardis_portal/blank_status.html', c))


def return_response_not_found(request):
    c = Context({'status': 'ERROR: Not Found', 'error': True})

    return HttpResponseNotFound(render_response_index(request,
                                'tardis_portal/blank_status.html', c))


def return_response_error_message(request, redirect_path, message):
    c = Context({'status': message, 'error': True})

    return HttpResponseServerError(render_response_index(request,
                                   redirect_path, c))


def logout(request):
    try:
        del request.session['username']
        del request.session['password']
        if 'datafileResults' in request.session:
            del request.session['datafileResults']
    except KeyError:
        pass

    c = Context({})

    return HttpResponse(render_response_index(request,
                        'tardis_portal/index.html', c))


def get_accessible_experiments(user_id):

    experiments = None

    # from stackoverflow question 852414

    from django.db.models import Q

    user = User.objects.get(id=user_id)

    queries = [Q(id=group.name) for group in user.groups.all()]

    if queries:
        query = queries.pop()

        for item in queries:
            query |= item

        experiments = Experiment.objects.filter(query)

    return experiments


def get_accessible_datafiles_for_user(experiments):

    # from stackoverflow question 852414

    from django.db.models import Q

    if experiments is not None:
        queries = [Q(dataset__experiment__id=e.id) for e in experiments]

        query = queries.pop()

        for item in queries:
            query |= item

        dataset_files = Dataset_File.objects.filter(query)

        return dataset_files
    else:
        return []


def get_owned_experiments(user_id):

    experiments = \
        Experiment.objects.filter(experiment_owner__user__pk=user_id)

    return experiments


def has_experiment_ownership(experiment_id, user_id):
    try:
        experiment = Experiment.objects.get(pk=experiment_id)
    except Experiment.DoesNotExist, e:
        return False

    eo = Experiment_Owner.objects.filter(experiment=experiment,
            user=user_id)

    if eo:
        return True
    else:
        return False


# custom decorator
def experiment_ownership_required(f):

    def wrap(request, *args, **kwargs):

        # if user isn't logged in it will redirect to login page

        if not request.user.is_authenticated():
            return HttpResponseRedirect('/login')
        if not has_experiment_ownership(kwargs['experiment_id'],
                request.user.pk):
            return return_response_error(request)

        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


# custom decorator
def experiment_access_required(f):

    def wrap(request, *args, **kwargs):

        if not has_experiment_access(kwargs['experiment_id'],
                request.user):

            # if user isn't logged in it will redirect to login page

            if not request.user.is_authenticated():
                return HttpResponseRedirect('/login')
            else:
                return return_response_error(request)

        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


# custom decorator
def dataset_access_required(f):

    def wrap(request, *args, **kwargs):
        if not has_dataset_access(kwargs['dataset_id'], request.user):

            # if user isn't logged in it will redirect to login page

            if not request.user.is_authenticated():
                return HttpResponseRedirect('/login')
            else:
                return return_response_error(request)

        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


# custom decorator
def datafile_access_required(f):

    def wrap(request, *args, **kwargs):
        if not has_datafile_access(kwargs['dataset_file_id'],
                                   request.user):

            # if user isn't logged in it will redirect to login page

            if not request.user.is_authenticated():
                return HttpResponseRedirect('/login')
            else:
                return return_response_error(request)

        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def has_experiment_access(experiment_id, user):

    # public route
    try:
        e = Experiment.objects.get(id=experiment_id)

        if e.public:
            return True
    except Experiment.DoesNotExist, ge:
        pass

    if not user.is_authenticated():
        return False

    g = Group.objects.filter(name=experiment_id, user__id=user.pk)

    if g:
        return True
    else:
        return False


def has_dataset_access(dataset_id, user):

    experiment = Experiment.objects.get(dataset__pk=dataset_id)

    if experiment.public:
        return True

    if not user.is_authenticated():
        return False

    g = Group.objects.filter(name=str(experiment.id), user__pk=user.pk)

    if g:
        return True
    else:
        return False


def has_datafile_access(dataset_file_id, user):

    df = Dataset_File.objects.get(id=dataset_file_id)

    if df.dataset.experiment.public:
        return True

    if not user.is_authenticated():
        return False

    g = Group.objects.filter(name=df.dataset.experiment.id,
                             user__pk=user.pk)

    if g:
        return True
    else:
        return False


def in_group(user, group):
    """Returns True/False if the user is in the given group(s).
    Usage::

        {% if user|in_group:"Friends" %}
        or
        {% if user|in_group:"Friends,Enemies" %}
        {% endif %}

    You can specify a single group or comma-delimited list.
    No white space allowed.

    """

    group_list = [group.name]

    user_groups = []

    for group in user.groups.all():
        user_groups.append(str(group.name))

    #logger.debug(group_list)
    #logger.debug(user_groups)

    if filter(lambda x: x in user_groups, group_list):
        return True
    else:
        return False


def index(request):

    status = ''
    c = Context(
        {'status': status,
         'searchDatafileSelectionForm': getNewSearchDatafileSelectionForm()})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/index.html', c))

def index_ansto(request):

    status = ''

    c = Context(
        {'status': status,
         'searchDatafileSelectionForm': getNewSearchDatafileSelectionForm()})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/index_ansto.html', c))


def site_settings(request):

    if request.method == 'POST':  # If the form has been submitted...
        if 'username' in request.POST and 'password' in request.POST:

            username = request.POST['username']
            password = request.POST['password']

            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_staff:

                    x509 = open(settings.GRID_PROXY_FILE, 'r')

                    c = Context({'baseurl'
                                : request.build_absolute_uri('/'),
                                'proxy': x509.read(), 'filestorepath'
                                : settings.FILE_STORE_PATH})
                    return HttpResponse(render_response_index(request,
                            'tardis_portal/site_settings.xml', c),
                            mimetype='application/xml')
                else:
                    return return_response_error(request)
            else:
                return return_response_error(request)
        else:
            return return_response_error(request)
    else:
        return return_response_error(request)


def display_experiment_image(
    request,
    experiment_id,
    parameterset_id,
    parameter_name,
    ):

    # todo handle not exist

    experiment = Experiment.objects.get(pk=experiment_id)
    if not has_experiment_access(experiment.id, request.user):
        return return_response_error(request)

    image = ExperimentParameter.objects.get(name__name=parameter_name,
                                            parameterset=parameterset_id)

    return HttpResponse(b64decode(image.string_value), mimetype='image/jpeg')


def display_dataset_image(
    request,
    dataset_id,
    parameterset_id,
    parameter_name,
    ):

    # todo handle not exist

    dataset = Dataset.objects.get(pk=dataset_id)
    if has_experiment_access(dataset.experiment.id, request.user):

        image = DatasetParameter.objects.get(name__name=parameter_name,
                parameterset=parameterset_id)

        import base64

        data = base64.b64decode(image.string_value)

        response = HttpResponse(data, mimetype='image/jpeg')

        return response
    else:
        return return_response_error(request)


def display_datafile_image(
    request,
    dataset_file_id,
    parameterset_id,
    parameter_name,
    ):

    # todo handle not exist

    datafile = Dataset_File.objects.get(pk=dataset_file_id)
    if has_experiment_access(datafile.dataset.experiment.id,
                             request.user):
        image = \
            DatafileParameter.objects.get(name__name=parameter_name,
                parameterset=parameterset_id)

        import base64

        data = base64.b64decode(image.string_value)

        response = HttpResponse(data, mimetype='image/jpeg')

        return response
    else:
        return return_response_error(request)


def about(request):

    c = Context({'subtitle': 'About', 'about_pressed': True,
                'nav': [{'name': 'About', 'link': '/about/'}],
                'searchDatafileSelectionForm':
                getNewSearchDatafileSelectionForm()})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/about.html', c))


def partners(request):

    c = Context({})

    return HttpResponse(render_response_index(request,
                        'tardis_portal/partners.html', c))


@experiment_access_required
def view_experiment(request, experiment_id):

    try:
        experiment = Experiment.objects.get(pk=experiment_id)
        author_experiments = experiment.author_experiment_set.all()

        datafiles = \
            Dataset_File.objects.filter(dataset__experiment=experiment_id)

        size = 0
        for dataset in experiment.dataset_set.all():
            for df in dataset.dataset_file_set.all():
                try:
                    size = size + long(df.size)
                except:
                    pass

        owners = None
        try:
            owners = \
                Experiment_Owner.objects.filter(experiment=experiment)
        except Experiment_Owner.DoesNotExist, eo:
            pass

        protocols = [df['protocol'] for df in
                     datafiles.values('protocol').distinct()]

        c = Context({
            # 'totalfilesize': datafiles.aggregate(Sum('size'))['size__sum'],
            'experiment': experiment,
            'authors': author_experiments,
            'datafiles': datafiles,
            'subtitle': experiment.title,
            'owners': owners,
            'size': size,
            'protocols': protocols,
            'upload_complete_url':
                reverse('tardis.tardis_portal.views.upload_complete'),
            'nav': [{'name': 'Data', 'link': '/experiment/view/'},
                    {'name': experiment.title, 'link'
                    : '/experiment/view/' + str(experiment.id) + '/'}],
            'searchDatafileSelectionForm'
                : getNewSearchDatafileSelectionForm(),
            'is_owner': has_experiment_ownership(experiment.id, request.user.id),
            })
    except Experiment.DoesNotExist, de:
        return return_response_not_found(request)

    return HttpResponse(render_response_index(request,
                        'tardis_portal/view_experiment.html', c))


def experiment_index(request):

    experiments = None

    # if logged in

    if request.user.is_authenticated():
        experiments = get_accessible_experiments(request.user.id)
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
        'data_pressed': True,
        'searchDatafileSelectionForm':
            getNewSearchDatafileSelectionForm()})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/experiment_index.html', c))


# todo complete....
def ldap_login(request):
    from django.contrib.auth import authenticate, login

    # if user exists then check if ldap: try log in through ldap, else try log
    # in usual way, either way login

    # TODO: put me in SETTINGS

    if 'username' in request.POST and 'password' in request.POST:
        username = request.POST['username']
        password = request.POST['password']

        next = '/'

        # TODO: this block will need fixing later as the expected functionality
        #       this condition is supposed to provide does not work

        if 'next' in request.POST:
            next = request.POST['next']

        c = Context({'searchDatafileSelectionForm'
                    : getNewSearchDatafileSelectionForm()})

        error_template_redirect = 'tardis_portal/login.html'

        if settings.LDAP_ENABLE:
            try:
                u = User.objects.get(username=username)

                try:
                    if u.get_profile().authcate_user:
                        if ldap_auth.authenticate_user_ldap(username,
                                password):
                            u.backend = \
                                'django.contrib.auth.backends.ModelBackend'
                            login(request, u)
                            return HttpResponseRedirect(next)
                        else:
                            return return_response_error_message(request,
                                    error_template_redirect,
                                    "Sorry, username and password don't match"
                                    )
                    else:
                        if authenticate(username=username,
                                password=password):
                            u.backend = \
                                'django.contrib.auth.backends.ModelBackend'
                            login(request, u)
                            return HttpResponseRedirect(next)
                        else:
                            return return_response_error_message(request,
                                    error_template_redirect,
                                    "Sorry, username and password don't match"
                                    )
                except UserProfile.DoesNotExist, ue:
                    if authenticate(username=username,
                                    password=password):
                        u.backend = \
                            'django.contrib.auth.backends.ModelBackend'
                        login(request, u)
                        return HttpResponseRedirect(next)
                    else:
                        return return_response_error_message(request,
                                error_template_redirect,
                                "Sorry, username and password don't match"
                                )
            except User.DoesNotExist, ue:
                if ldap_auth.authenticate_user_ldap(username, password):
                    email = ldap_auth.get_ldap_email_for_user(username)

                    from random import choice
                    import string

                    # random password todo make function

                    random_password = ''
                    chars = string.letters + string.digits

                    for i in range(8):
                        random_password = random_password \
                            + choice(chars)

                    u = User.objects.create_user(username, email,
                            random_password)
                    up = UserProfile(authcate_user=True, user=u)
                    up.save()

                    u.backend = \
                        'django.contrib.auth.backends.ModelBackend'

                    # TODO: consolidate

                    login(request, u)
                    return HttpResponseRedirect(next)
                else:
                    return return_response_error_message(request,
                            error_template_redirect,
                            "Sorry, username and password don't match")
        u = authenticate(username=username, password=password)
        if u:
            u.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, u)
            return HttpResponseRedirect(next)
        else:
            return return_response_error_message(request,
                    error_template_redirect,
                    "Sorry, username and password don't match")

    c = Context({'searchDatafileSelectionForm'
                : getNewSearchDatafileSelectionForm()})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/login.html', c))


@transaction.commit_on_success()
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
        response['Location'] = \
            request.build_absolute_uri('/experiment/view/' + str(eid))

        return response


def _registerExperimentDocument(filename, created_by, expid=None,
                                owners=[], username=None):
    '''
    Register the experiment document.

    Arguments:
    filename -- path of the document to parse (METS or notMETS)
    created_by -- a User instance
    expid -- the experiment ID to use
    owner -- a list of owners
    username -- the user who is the owner

    Returns:
    The experiment ID

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

    g = Group(name=eid)
    g.save()

    # for each PI
    for owner in owners:
        owner = urllib.unquote_plus(owner)
        u = None
        # try get user from email
        if settings.LDAP_ENABLE:
            u = ldap_auth.get_or_create_user_ldap(owner)
        else:
            u = User.objects.get(username=username)

        # if exist, assign to group
        if u:
            logger.debug('registering owner: ' + owner)
            e = Experiment.objects.get(pk=eid)
            exp_owner = Experiment_Owner(experiment=e,
                                         user=u)
            exp_owner.save()
            u.groups.add(g)

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
            experiment_owner = form.cleaned_data['experiment_owner']
            originid = form.cleaned_data['originid']

            from_url = None
            if 'form_url' in request.POST:
                from_url = request.POST['from_url']

            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            if user is not None:
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

            dir = settings.FILE_STORE_PATH + '/' + str(eid)

            # TODO: this entire function needs a fancy class with functions for
            # each part..

            import os
            if not os.path.exists(dir):
                os.makedirs(dir)
                os.system('chmod g+w ' + dir)

            filename = dir + '/METS.xml'
            file = open(filename, 'wb+')
            for chunk in xmldata.chunks():
                file.write(chunk)
            file.close()


            class RegisterThread(threading.Thread):
                def run(self):
                    logger.info('=== processing experiment %s: START' % eid)
                    owners = request.POST.getlist('experiment_owner')
                    try:
                        _registerExperimentDocument(filename=filename,
                                                    created_by=user, expid=eid,
                                                    owners=owners,
                                                    username=username)
                        logger.info('=== processing experiment %s: DONE' % eid)
                    except:
                        logger.exception('=== processing experiment %s: FAILED!' % eid)


            RegisterThread().start()

            logger.debug('Sending file request')

            if from_url:


                class FileTransferThread(threading.Thread):

                    def run(self):
                        # todo remove hard coded u/p for sync transfer....
                        logger.debug('started transfer thread')
                        file_transfer_url = from_url + '/file_transfer/'
                        data = urllib.urlencode({
                            'originid': str(originid),
                            'eid': str(eid),
                            'site_settings_url'
                                : request.build_absolute_uri('/site-settings.xml/'
                                    ),
                            'username': str('synchrotron'),
                            'password': str('tardis'),
                            })
                        urllib.urlopen(file_transfer_url, data)


                FileTransferThread().start()

            logger.debug('returning response from main call')
            response = HttpResponse(str(eid), status=200)
            response['Location'] = \
                request.build_absolute_uri('/experiment/view/'
                    + str(eid))
            return response
    else:
        form = RegisterExperimentForm()  # An unbound form

    c = Context({
        'form': form,
        'status': status,
        'subtitle': 'Register Experiment',
        'searchDatafileSelectionForm'
            : getNewSearchDatafileSelectionForm(),
        })
    return HttpResponse(render_response_index(request,
                        'tardis_portal/register_experiment.html', c))


@datafile_access_required
def retrieve_parameters(request, dataset_file_id):

    parametersets = DatafileParameterSet.objects.all()
    parametersets = \
        parametersets.filter(dataset_file__pk=dataset_file_id)

    c = Context({'parametersets': parametersets})

    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/parameters.html', c))


@datafile_access_required
def retrieve_xml_data(request, dataset_file_id):
    from pygments import highlight
    from pygments.lexers import XmlLexer
    from pygments.formatters import HtmlFormatter

    xml_data = XML_data.objects.get(datafile__pk=dataset_file_id)

    formatted_xml = highlight(xml_data.data, XmlLexer(),
                              HtmlFormatter(style='default',
                              noclasses=True))

    c = Context({'formatted_xml': formatted_xml})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/xml_data.html', c))


@dataset_access_required
def retrieve_datafile_list(request, dataset_id):

    dataset_results = \
        Dataset_File.objects.filter(dataset__pk=dataset_id).order_by('filename'
            )

    filename_search = None

    if 'filename' in request.GET and len(request.GET['filename']) > 0:
        filename_search = request.GET['filename']
        dataset_results = \
            dataset_results.filter(url__icontains=filename_search)

    pgresults = 500
    if request.mobile:
        pgresults = 30
    else:
        pgresults = 500

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
        is_owner = has_experiment_ownership(experiment_id, request.user.id)

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

    experiments = get_owned_experiments(request.user.id)
    if experiments:
        experiments = experiments.order_by('title')

    c = Context({'experiments': experiments, 'subtitle'
                : 'Experiment Control Panel'})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/control_panel.html', c))


@login_required()
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

    c = Context({
        'experiments': experiments,
        'bodyclass': bodyclass,
        'searchDatafileSelectionForm': getNewSearchDatafileSelectionForm()})
    url = 'tardis_portal/search_experiment_results.html'
    return HttpResponse(render_response_index(request, url, c))


@login_required()
def search_quick(request):
    get = False
    experiments = Experiment.objects.all()
    experiments = Experiment.objects.order_by('title')

    if 'results' in request.GET:
        get = True
        if 'quicksearch' in request.GET \
            and len(request.GET['quicksearch']) > 0:
            experiments = \
                experiments.filter(title__icontains=request.GET['quicksearch'
                                   ]) \
                | experiments.filter(institution_name__icontains=request.GET['quicksearch'
                    ]) \
                | experiments.filter(author_experiment__author__name__icontains=request.GET['quicksearch'
                    ]) \
                | experiments.filter(pdbid__pdbid__icontains=request.GET['quicksearch'
                    ])

            experiments = experiments.distinct()

            logger.debug(experiments)

    c = Context({'submitted': get, 'experiments': experiments,
                'subtitle': 'Search Experiments'})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/search_experiment.html', c))


@login_required()
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

    # from django.db.models import Q
    logger.info('__getFilteredDatafiles: searchFilterData {0}'.format(searchFilterData))

    datafile_results = \
        get_accessible_datafiles_for_user(get_accessible_experiments(request.user.id))

    # there's no need to do any filtering if we didn't find any
    # datafiles that the user has access to

    if len(datafile_results) == 0:
        logger.info("__getFilteredDatafiles: user ",
                    "{0} ({1}) doesn\'t".format(request.user,
                                                request.user.id),
                    "access to any experiments")
        return datafile_results

    datafile_results = \
        datafile_results.filter(datafileparameterset__datafileparameter__name__schema__namespace__exact=constants.SCHEMA_DICT[searchQueryType]['datafile'
                                ]).distinct()

    # if filename is searchable which i think will always be the case...

    if searchFilterData['filename'] != '':
        datafile_results = \
            datafile_results.filter(filename__icontains=searchFilterData['filename'
                                    ])

    # TODO: might need to cache the result of this later on

    # get all the datafile parameters for the given schema
    parameters = [p for p in
                  ParameterName.objects.filter(schema__namespace__exact=constants.SCHEMA_DICT[searchQueryType]['datafile'
                  ])]

    datafile_results = __filterParameters(parameters, datafile_results,
            searchFilterData, 'datafileparameterset__datafileparameter')

    # get all the dataset parameters for given schema
    parameters = [p for p in
                  ParameterName.objects.filter(schema__namespace__exact=constants.SCHEMA_DICT[searchQueryType]['dataset'
                  ])]

    datafile_results = __filterParameters(parameters, datafile_results,
            searchFilterData,
            'dataset__datasetparameterset__datasetparameter')

    # let's sort it in the end

    if datafile_results:
        datafile_results = datafile_results.order_by('filename')
    logger.debug("results: {0}".format(datafile_results))
    return datafile_results


@login_required()
def __getFilteredExperiments(request, searchFilterData):
    """Filter the list of experiments using the cleaned up searchFilterData.

    Arguments:
    request -- the HTTP request
    searchFilterData -- the cleaned up search experiment form data

    Returns:
    A list of experiments as a result of the query or None if the provided
      search request is invalid

    """

    #from django.db.models import Q

    experiments = get_accessible_experiments(request.user.id)

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
        author_experiment__author__name__icontains=searchFilterData['creator'])

    date = searchFilterData['date']
    if not date == None:
        experiments = \
            experiments.filter(start_time__lt=date, end_time__gt=date)

    # initialise the extra experiment parameters
    parameters = []

    # get all the experiment parameters
    for experimentSchema in constants.EXPERIMENT_SCHEMAS:
        parameters += ParameterName.objects.filter(
            schema__namespace__exact=experimentSchema)

    experiments = __filterParameters(parameters, experiments,
            searchFilterData, 'experimentparameterset__experimentparameter')

    # let's sort it in the end
    if experiments:
        experiments = experiments.order_by('title')

    return experiments


def __filterParameters(
    parameters,
    datafile_results,
    searchFilterData,
    paramType,
    ):
    """Go through each parameter and apply it as a filter (together with its
    specified comparator) on the provided list of datafiles.

    Arguments:
    parameters -- list of ParameterNames model
    datafile_results -- list of datafile to apply the filter
    searchFilterData -- the cleaned up search form data
    paramType -- either 'datafile' or 'dataset'

    Returns:
    A list of datafiles as a result of the query or None if the provided search
      request is invalid

    """

    for parameter in parameters:
        kwargs = {paramType + '__name__name__icontains': parameter.name}
        try:

            # if parameter is a string...

            if not parameter.is_numeric:
                if searchFilterData[parameter.name] != '':

                    # let's check if this is a field that's specified to be
                    # displayed as a dropdown menu in the form

                    if parameter.choices != '':
                        if searchFilterData[parameter.name] != '-':
                            kwargs[paramType + '__string_value__iexact'
                                   ] = searchFilterData[parameter.name]
                    else:
                        if parameter.comparison_type \
                            == ParameterName.EXACT_VALUE_COMPARISON:
                            kwargs[paramType + '__string_value__iexact'
                                   ] = searchFilterData[parameter.name]
                        elif parameter.comparison_type \
                            == ParameterName.CONTAINS_COMPARISON:

                            # we'll implement exact comparison as 'icontains'
                            # for now

                            kwargs[paramType
                                   + '__string_value__icontains'] = \
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
            else:

                   # parameter.is_numeric:

                if parameter.comparison_type \
                    == ParameterName.RANGE_COMPARISON:
                    fromParam = searchFilterData[parameter.name + 'From'
                            ]
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

                        kwargs[paramType + '__numerical_value__range'
                               ] = (fromParam is None
                                    and constants.FORM_RANGE_LOWEST_NUM
                                    or fromParam, toParam is not None
                                    and toParam
                                    or constants.FORM_RANGE_HIGHEST_NUM)
                elif searchFilterData[parameter.name] is not None:

                    # if parameter is an number and we want to handle other
                    # type of number comparisons

                    if parameter.comparison_type \
                        == ParameterName.EXACT_VALUE_COMPARISON:
                        kwargs[paramType + '__numerical_value__exact'
                               ] = searchFilterData[parameter.name]
                    elif parameter.comparison_type \
                        == ParameterName.GREATER_THAN_COMPARISON:

                    # TODO: is this really how not equal should be declared?
                    # elif parameter.comparison_type ==
                    #       ParameterName.NOT_EQUAL_COMPARISON:
                    #   datafile_results = \
                    #       datafile_results.filter(
                    #  datafileparameter__name__name__icontains=parameter.name)
                    #       .filter(
                    #  ~Q(datafileparameter__numerical_value=searchFilterData[
                    #       parameter.name]))

                        kwargs[paramType + '__numerical_value__gt'] = \
                            searchFilterData[parameter.name]
                    elif parameter.comparison_type \
                        == ParameterName.GREATER_THAN_EQUAL_COMPARISON:
                        kwargs[paramType + '__numerical_value__gte'] = \
                            searchFilterData[parameter.name]
                    elif parameter.comparison_type \
                        == ParameterName.LESS_THAN_COMPARISON:
                        kwargs[paramType + '__numerical_value__lt'] = \
                            searchFilterData[parameter.name]
                    elif parameter.comparison_type \
                        == ParameterName.LESS_THAN_EQUAL_COMPARISON:
                        kwargs[paramType + '__numerical_value__lte'] = \
                            searchFilterData[parameter.name]
                    else:

                        # if comparison_type on a numeric is a comparison type
                        # that can only be applied to a string value, we'll
                        # default to just using 'exact' comparison

                        kwargs[paramType + '__numerical_value__exact'
                               ] = searchFilterData[parameter.name]
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

        # else:
        #    # TODO: what do we need to do if the user didn't provide a page to
        #            display?
        #    pass

    # TODO: remove this later on when we have a more generic search form

    if searchQueryType == 'mx':
        url = 'tardis_portal/search_datafile_form_mx.html'

    from itertools import groupby

    # sort the fields in the form as it will make grouping the related fields
    # together in the next step easier

    sortedSearchForm = sorted(searchForm, lambda x, y: cmp(x.name,
                              y.name))

    # modifiedSearchForm will be used to customise how the range type of fields
    # will be displayed. range type of fields will be displayed side by side.

    modifiedSearchForm = [list(g) for (k, g) in
                          groupby(sortedSearchForm, lambda x: \
                          x.name.rsplit('To')[0].rsplit('From')[0])]

    # the searchForm will be used by custom written templates whereas the
    # modifiedSearchForm will be used by the 'generic template' that the
    # dynamic search datafiles form uses.
    c = Context({
        'searchForm': searchForm,
        'modifiedSearchForm': modifiedSearchForm,
        'searchDatafileSelectionForm':
        getNewSearchDatafileSelectionForm()})
    return HttpResponse(render_response_index(request, url, c))


def __forwardToSearchExperimentFormPage(request):
    """Forward to the search experiment form page."""

    searchForm = __getSearchExperimentForm(request)

    c = Context({'searchForm': searchForm, 'searchDatafileSelectionForm'
                : getNewSearchDatafileSelectionForm()})
    url = 'tardis_portal/search_experiment_form.html'
    return HttpResponse(render_response_index(request, url, c))


def __getSearchDatafileForm(request, searchQueryType):
    """Create the search datafile form based on the HTTP GET request.

    Arguments:
    request -- The HTTP request object
    searchQueryType -- The search query type: 'mx' or 'saxs'

    Returns:
    The supported search datafile form

    Throws:
    UnsupportedSearchQueryTypeError is the provided searchQueryType is not
    supported

    """

    try:
        SearchDatafileForm = createSearchDatafileForm(searchQueryType)
        form = SearchDatafileForm(request.GET)
        return form
    except UnsupportedSearchQueryTypeError, e:
        raise e


def __getSearchExperimentForm(request):
    """Create the search experiment form.

    Arguments:
    request -- The HTTP request object

    Returns:
    The search experiment form

    """

    SearchExperimentForm = createSearchExperimentForm()
    form = SearchExperimentForm(request.GET)
    return form


def __processDatafileParameters(request, searchQueryType, form):
    """Validate the provided datafile search request and return search results.

    Arguments:
    request -- The HTTP request object
    searchQueryType -- The search query type
    form -- The search form to use

    Returns:
    A list of datafiles as a result of the query or None if the provided search
      request is invalid

    Throws:
    SearchQueryTypeUnprovidedError if searchQueryType is not in the HTTP GET
        request
    UnsupportedSearchQueryTypeError is the provided searchQueryType is not
        supported

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

    Arguments:
    request -- The HTTP request object
    form -- The search form to use

    Returns:
    A list of experiments as a result of the query or None if the provided
      search request is invalid

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


@login_required()
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

    if 'page' not in request.GET and 'type' in request.GET \
        and len(request.GET) > 1:

        # display the 1st page of the results

        form = __getSearchDatafileForm(request, searchQueryType)
        datafile_results = __processDatafileParameters(
            request, searchQueryType, form)
        if datafile_results is not None:
            bodyclass = 'list'
        else:
            return __forwardToSearchDatafileFormPage(request,
                    searchQueryType, form)
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
            return __forwardToSearchDatafileFormPage(request,
                    searchQueryType)

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
        'nav': [{'name': 'Search Datafile', 'link': '/search/datafile/'
                }],
        'bodyclass': bodyclass,
        'search_pressed': True,
        'searchDatafileSelectionForm'
            : getNewSearchDatafileSelectionForm(),
        })
    url = 'tardis_portal/search_datafile_results.html'
    return HttpResponse(render_response_index(request, url, c))


@login_required()
def retrieve_user_list(request):

    users = User.objects.all().order_by('username')

    c = Context({'users': users})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/user_list.html', c))


@experiment_ownership_required
def retrieve_access_list(request, experiment_id):

    users = \
        User.objects.filter(groups__name=experiment_id).order_by('username'
            )

    c = Context({'users': users, 'experiment_id': experiment_id})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/ajax/access_list.html', c))


@experiment_ownership_required
def add_access_experiment(request, experiment_id, username):
    try:
        u = User.objects.get(username=username)

        g = Group.objects.get(name=experiment_id)

        if not in_group(u, g):
            u.groups.add(g)

            c = Context({'user': u, 'experiment_id': experiment_id})
            return HttpResponse(render_response_index(request,
                                'tardis_portal/ajax/add_user_result.html'
                                , c))
        else:
            return return_response_error(request)
    except User.DoesNotExist, ue:

        return return_response_not_found(request)
    except Group.DoesNotExist, ge:
        return return_response_not_found(request)

    return return_response_error(request)


@experiment_ownership_required
def remove_access_experiment(request, experiment_id, username):

    try:
        u = User.objects.get(username=username)

        g = Group.objects.get(name=experiment_id)

        e = Experiment.objects.get(pk=experiment_id)

        if in_group(u, g):
            u.groups.remove(g)

            try:
                eo = Experiment_Owner.objects.filter(experiment=e,
                        user=u)
                eo.delete()
            except Experiment_Owner.DoesNotExist, eo:
                pass

            c = Context({})
            return HttpResponse(render_response_index(request,
                                'tardis_portal/ajax/remove_user_result.html'
                                , c))
        else:
            return return_response_error(request)
    except User.DoesNotExist, ue:

        return return_response_not_found(request)
    except Group.DoesNotExist, ge:
        return return_response_not_found(request)
    except Experiment.DoesNotExist, ge:
        return return_response_not_found(request)

    return return_response_error(request)


@experiment_ownership_required
def publish_experiment(request, experiment_id):

    experiment = Experiment.objects.get(id=experiment_id)

    if not experiment.public:
        filename = settings.FILE_STORE_PATH + '/' + experiment_id \
            + '/METS.XML'

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
                             'PyMOTW (http://www.doughellmann.com/PyMOTW/)'
                             )
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
        size = size + long(df.size)

    public_datafile_size = size

    c = Context({'public_datafiles': len(public_datafiles),
                'public_experiments': len(public_experiments),
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
                    except Schema.DoesNotExist, s:
                        schema_db = Schema(namespace=schema)
                        schema_db.save()
                else:
                    part = line.split('^')
                    if len(part) == 4:

                        is_numeric = False
                        if part[3].strip(' \n\r') == 'True':
                            is_numeric = True

                        pn = ParameterName(schema=schema_db,
                                name=part[0], full_name=part[1],
                                units=part[2], is_numeric=is_numeric)
                        pn.save()

                i = i + 1

            return HttpResponse('OK')
    else:
        form = ImportParamsForm()

    c = Context({'form': form, 'subtitle': 'Import Parameters'})
    return HttpResponse(render_response_index(request,
                        'tardis_portal/import_params.html', c))


def staging_traverse(staging=settings.STAGING_PATH):
    """
    Recurse through directories and form HTML list tree for jtree

    :param staging: the path to begin traversing
    :type staging: string
    :rtype: string
    """

    ul = '<ul><li id="phtml_1"><a>My Files</a><ul>'
    for f in os.listdir(staging):
        ul = ul + traverse(path.join(staging, f), staging)
    return ul + '</ul></li></ul>'


def traverse(pathname, dirname=settings.STAGING_PATH):
    """
    Traverse a path and return a nested group of unordered list HTML tags::

       <ul>
         <li id="dir2/file2"><a>file2</a></li>
         <li id="dir2/file3"><a>file3</a></li>
         <li id="dir2/subdir"><a>subdir</a>
           <ul>
             <li id="dir2/subdir/file4"><a>file4</a></li>
           </ul>
         </li>
       </ul>

    :param pathname: the directory to traverse
    :type pathname: string
    :param dirname: the root directory of the traversal
    :type dirname: string
    :rtype: string
    """

    li = '<li id="%s"><a>%s</a>' % (path.relpath(pathname, dirname),
                                    path.basename(pathname))
    if path.isfile(pathname):
        return li + '</li>'
    if path.isdir(pathname):
        ul = '<ul>'
        for f in os.listdir(pathname):
            ul = ul + traverse(path.join(pathname, f), dirname)
        return li + ul + '</ul></li>'
    return ''


def stage_files(
    datafiles,
    experiment_id,
    staging=settings.STAGING_PATH,
    store=settings.FILE_STORE_PATH,
    ):
    """
    move files from the staging area to the dataset.
    """

    experiment_path = path.join(store, str(experiment_id))
    if not os.path.exists(experiment_path):
        os.makedirs(experiment_path)

    for datafile in datafiles:
        urlpath = datafile.url.partition('//')[2]
        todir = path.join(experiment_path, path.split(urlpath)[0])
        if not os.path.exists(todir):
            os.makedirs(todir)

        copyfrom = path.join(staging, urlpath)  # to be url
        copyto = path.join(experiment_path, urlpath)
        if path.exists(copyto):
            logger.error("can't stage %s destination exists" % copyto)

            # TODO raise error

            continue

        logger.debug('staging file: %s to %s' % (copyfrom, copyto))
        datafile.size = os.path.getsize(copyfrom)
        datafile.save()
        shutil.move(copyfrom, copyto)


@login_required
def create_experiment(request,
                      template_name='tardis_portal/create_experiment.html'):
    """
    Create a new experiment view.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param template_name: the path of the template to render
    :type template_name: string
    :rtype: :class:`django.http.HttpResponse`
    """
    if request.method == 'POST':
        form = FullExperiment(request.POST, request.FILES)
        if form.is_valid():
            full_experiment = form.save(commit=False)

            for ds_f in full_experiment['dataset_files']:
                filepath = ds_f.filename
                ds_f.url = 'file://' + filepath
                ds_f.filename = os.path.basename(filepath)
                ds_f.size = 0
                ds_f.protocol = ''

            # group/owner assignment stuff, soon to be replaced

            experiment = full_experiment['experiment']
            full_experiment.save_m2m()

            g = Group(name=experiment.id)
            g.save()
            exp_owner = Experiment_Owner(experiment=experiment,
                    user=request.user)
            exp_owner.save()
            request.user.groups.add(g)

            stage_files(full_experiment['dataset_files'], experiment.id)

            return HttpResponseRedirect(experiment.get_absolute_url())
    else:
        form = FullExperiment()

    c = Context({
        'subtitle': 'Create Experiment',
        'directory_listing': staging_traverse(),
        'user_id': request.user.id,
        'form': form,
        })

    return HttpResponse(render_response_index(request, template_name, c))


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

def upload(
    request,
    dataset_id,
    *args,
    **kwargs
    ):
    """
    Uploads a datafile to the store and datafile metadata
    :param dataset_id: the dataset_id
    :type dataset_id: integer
    :rtype: boolean true if successful
    """

    dataset = Dataset.objects.get(id=dataset_id)

    logger.debug('called upload')
    if request.method == 'POST':
        logger.debug('got POST')
        if request.FILES:

            uploaded_file_post = request.FILES['Filedata']

            print 'about to write uploaded file'
            filepath = write_uploaded_file_to_dataset(dataset,
                    uploaded_file_post)
            print filepath

            add_datafile_to_dataset(dataset, filepath,
                                    uploaded_file_post.size)
            print 'added datafile to dataset'

    return HttpResponse('True')


def write_uploaded_file_to_dataset(dataset, uploaded_file_post):
    """
    Writes file POST data to the dataset directory in the file store
    :param dataset_id: dataset who's directory to be written to
    :type dataset: models.Model
    :rtype: the path of the file written to
    """

    filename = uploaded_file_post.name

    experiment_path = path.join(settings.FILE_STORE_PATH,
                                str(dataset.experiment.id))

    dataset_path = path.join(experiment_path, str(dataset.id))

    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    copyto = dataset_path + '/' + filename

    copyto = duplicate_file_check_rename(copyto)

    uploaded_file = open(copyto, 'wb+')

    for chunk in uploaded_file_post.chunks():
        uploaded_file.write(chunk)

    uploaded_file.close()

    return copyto


def duplicate_file_check_rename(copyto):
    """
    Checks if the destination for the file already exists and returns
    a non-conflicting name

    :param copyto: The destination path to check
    :type copyto: string
    :rtype: The new non-conflicting path (the original path if no conflicts)
    """
    i = 1
    base, filename = path.split(copyto)
    name, ext = path.splitext(filename)
    result = copyto

    while path.exists(result):
        logger.debug('%s destination exists' % result)
        result = path.join(base, "{0}_{1}{2}".format(name, i, ext))
        i += 1
    return result


def add_datafile_to_dataset(dataset, filepath, size):
    """
    Adds datafile metadata to a dataset
    :param dataset_id: dataset who's directory to be written to
    :type dataset: models.Model
    :param filepath: The full os path to the file
    :type filepath: string
    :param size: The file size in bytes
    :type size: string
    :rtype: The new datafile object
    """

    experiment_path = path.join(settings.FILE_STORE_PATH,
                                str(dataset.experiment.id))

    dataset_path = path.join(experiment_path, str(dataset.id))

    urlpath = 'file:/' + filepath[len(experiment_path):]
    filename = urlpath.rpartition('/')[2]

    datafile = Dataset_File(dataset=dataset, filename=filename,
                            url=urlpath, size=size, protocol='')

    datafile.save()

    return datafile


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
    :rtype: A view containing an Uploadify *create files* button
    """
    url = reverse('tardis.tardis_portal.views.upload_complete')
    c = Context({'upload_complete_url': url, 'dataset_id': dataset_id})
    return render_to_response(template_name, c)


def search_equipment(request):
    if request.method == 'POST':
        form = EquipmentSearchForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            q = Equipment.objects.all()
            if data['key']:
                q = q.filter(key__icontains=data['key'])
            if data['description']:
                q = q.filter(description__icontains=data['description'])
            if data['make']:
                q = q.filter(make__icontains=data['make'])
            if data['serial']:
                q = q.filter(serial__icontains=data['serial'])
            if data['type']:
                q = q.filter(type__icontains=data['type'])

            c = Context({'object_list': q,
                         'searchDatafileSelectionForm':
                         getNewSearchDatafileSelectionForm()})
            return render_to_response('tardis_portal/equipment_list.html', c)
    else:
        form = EquipmentSearchForm()

    c = Context({'form': form,
                 'searchDatafileSelectionForm':
                 getNewSearchDatafileSelectionForm()})
    return render_to_response('tardis_portal/search_equipment.html', c)
