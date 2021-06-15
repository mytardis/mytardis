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
# pylint: disable=R1702
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.http import HttpResponse, HttpRequest
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.conf import settings

from ..models import Experiment, Dataset, DataFile, GroupAdmin
from ..shortcuts import return_response_error


def get_accessible_experiments(request):
    return Experiment.safe.all(request.user)


def get_accessible_experiments_for_dataset(request, dataset_id):
    experiments = Experiment.safe.all(request.user)
    return experiments.filter(datasets__id=dataset_id)


def get_shared_experiments(request):
    return Experiment.safe.shared(request.user)


def get_owned_experiments(request):
    return Experiment.safe.owned(request.user)


def get_accessible_datafiles_for_user(request):
    experiments = get_accessible_experiments(request)
    experiment_ids = list(experiments.values_list('id', flat=True))

    if len(experiment_ids) == 0:
        return DataFile.objects.none()

    return DataFile.objects.filter(
        Q(dataset__experiments__id__in=experiment_ids))


def has_ownership(request, obj_id, ct_type):
    if ct_type == 'experiment':
        return Experiment.safe.owned(request.user).filter(
            pk=obj_id).exists()
    if ct_type == 'dataset':
        return Dataset.safe.owned(request.user).filter(
            pk=obj_id).exists()
    if ct_type == 'datafile':
        return DataFile.safe.owned(request.user).filter(
            pk=obj_id).exists()

def has_dataset_ownership(request, dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)
    return any(has_experiment_ownership(request, experiment.id)
               for experiment in dataset.experiments.all())





def has_experiment_access(request, experiment_id):
    try:
        experiment = Experiment.objects.get(id=experiment_id)
    except Experiment.DoesNotExist:
        return False
    return request.user.has_perm('tardis_acls.view_experiment', experiment)


def has_experiment_write(request, experiment_id):
    return has_write_permissions(request, experiment_id)


def has_experiment_download_access(request, experiment_id):

    if Experiment.safe.owned_and_shared(request.user) \
                      .filter(id=experiment_id) \
                      .exists():

        return True
    exp = Experiment.objects.get(id=experiment_id)
    return Experiment.public_access_implies_distribution(exp.public_access)





def has_dataset_access(request, dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)

    return any(has_experiment_access(request, experiment.id)
               for experiment in dataset.experiments.all())


def has_dataset_write(request, dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)
    if dataset.immutable:
        return False
    return any(has_experiment_write(request, experiment.id)
               for experiment in dataset.experiments.all())


def has_dataset_download_access(request, dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)
    return any(has_experiment_download_access(request, experiment.id)
               for experiment in dataset.experiments.all())


def has_datafile_access(request, datafile_id):
    try:
        dataset = Dataset.objects.get(datafile=datafile_id)
    except Dataset.DoesNotExist:
        return False
    return has_dataset_access(request, dataset.id)


def has_datafile_download_access(request, datafile_id):
    dataset = Dataset.objects.get(datafile=datafile_id)
    return has_dataset_download_access(request, dataset.id)


def has_read_or_owner_ACL(request, experiment_id):
    """
    Check whether the user has read access to the experiment -
    this means either
    they have been granted read access, or that they are the owner.

    NOTE:
    This does not check whether the experiment is public or not, which means
    even when the experiment is public, this method does not automatically
    returns true.

    As such, this method should NOT be used to check whether the user has
    general read permission.
    """
    from datetime import datetime
    from .localdb_auth import django_user

    experiment = Experiment.safe.get(request.user, experiment_id)

    # does the user own this experiment
    query = Q(content_type=experiment.get_ct(),
              object_id=experiment.id,
              pluginId=django_user,
              entityId=str(request.user.id),
              isOwner=True)

    # check if there is a user based authorisation role
    query |= Q(content_type=experiment.get_ct(),
               object_id=experiment.id,
               pluginId=django_user,
               entityId=str(request.user.id),
               canRead=True)\
               & (Q(effectiveDate__lte=datetime.today())
                  | Q(effectiveDate__isnull=True))\
               & (Q(expiryDate__gte=datetime.today())
                  | Q(expiryDate__isnull=True))

    # and finally check all the group based authorisation roles
    for name, group in request.user.userprofile.ext_groups:
        query |= Q(pluginId=name,
                   entityId=str(group),
                   content_type=experiment.get_ct(),
                   object_id=experiment.id,
                   canRead=True)\
                   & (Q(effectiveDate__lte=datetime.today())
                      | Q(effectiveDate__isnull=True))\
                   & (Q(expiryDate__gte=datetime.today())
                      | Q(expiryDate__isnull=True))

    # is there at least one ACL rule which satisfies the rules?
    from ..models.access_control import ExperimentACL
    acl = ExperimentACL.objects.filter(query)
    return bool(acl)


def has_write_permissions(request, experiment_id):
    experiment = Experiment.objects.get(id=experiment_id)
    return request.user.has_perm('tardis_acls.change_experiment', experiment)


def has_delete_permissions(request, experiment_id):
    experiment = Experiment.safe.get(request.user, experiment_id)
    return request.user.has_perm('tardis_acls.delete_experiment', experiment)


@login_required
def is_group_admin(request, group_id):
    return GroupAdmin.objects.filter(user=request.user,
                                     group__id=group_id).exists()


def group_ownership_required(f):
    """
    A decorator for Django views that validates if a user is a group admin
    or 'superuser' prior to further processing the request.
    Unauthenticated requests are redirected to the login page. If the
    user making the request satisfies none of these criteria, an error response
    is returned.

    :param f: A Django view function
    :type f: types.FunctionType
    :return: A Django view function
    :rtype: types.FunctionType
    """
    def wrap(request, *args, **kwargs):
        user = request.user
        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login?next=%s' % request.path)
        if not (is_group_admin(request, kwargs['group_id']) or
                user.is_superuser):
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def experiment_ownership_required(f):
    """
    A decorator for Django views that validates if a user is an owner of an
    experiment or 'superuser' prior to further processing the request.
    Unauthenticated requests are redirected to the login page. If the
    user making the request satisfies none of these criteria, an error response
    is returned.

    :param f: A Django view function
    :type f: types.FunctionType
    :return: A Django view function
    :rtype: types.FunctionType
    """
    def wrap(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return HttpResponseRedirect('/login?next=%s' % request.path)
        if not (has_experiment_ownership(request, kwargs['experiment_id']) or
                user.is_superuser):
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def experiment_access_required(f):

    def wrap(*args, **kwargs):
        # We find the request as either the first or second argument.
        # This is so it can be used for the 'get' method on class-based
        # views (where the first argument is 'self') and also with traditional
        # view functions (where the first argument is the request).
        # TODO: An alternative would be to create a mixin for the ExperimentView
        #       and similar classes, like AccessRequiredMixin
        request = args[0]
        if not isinstance(request, HttpRequest):
            request = args[1]

        if not has_experiment_access(request, kwargs['experiment_id']):
            return return_response_error(request)
        return f(*args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def experiment_download_required(f):

    def wrap(request, *args, **kwargs):
        if not has_experiment_download_access(
                request, kwargs['experiment_id']):
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def dataset_download_required(f):

    def wrap(request, *args, **kwargs):
        if not has_dataset_download_access(request, kwargs['dataset_id']):
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def dataset_access_required(f):

    def wrap(*args, **kwargs):
        # We find the request as either the first or second argument.
        # This is so it can be used for the 'get' method on class-based
        # views (where the first argument is 'self') and also with traditional
        # view functions (where the first argument is the request).
        # TODO: An alternative would be to create a mixin for the DatasetView
        #       and similar classes, like AccessRequiredMixin
        request = args[0]
        if not isinstance(request, HttpRequest):
            request = args[1]

        if not has_dataset_access(request, kwargs['dataset_id']):
            return return_response_error(request)
        return f(*args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def datafile_access_required(f):

    def wrap(request, *args, **kwargs):

        if not has_datafile_access(request, kwargs['datafile_id']):
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def write_permissions_required(f):

    def wrap(request, *args, **kwargs):

        if not has_write_permissions(request, kwargs['experiment_id']):
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def dataset_write_permissions_required(f):
    def wrap(request, *args, **kwargs):
        dataset_id = kwargs['dataset_id']
        if not has_dataset_write(request, dataset_id):
            if request.is_ajax():
                return HttpResponse("")
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def delete_permissions_required(f):

    def wrap(request, *args, **kwargs):

        if not has_delete_permissions(request, kwargs['experiment_id']):
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def upload_auth(f):
    def wrap(request, *args, **kwargs):
        from django.utils import timezone
        session_id = request.POST.get('session_id',
                                      request.COOKIES.get(
                                          settings.SESSION_COOKIE_NAME,
                                          None))
        sessions = Session.objects.filter(pk=session_id)
        if sessions and sessions[0].expire_date > timezone.now():
            try:
                request.user = User.objects.get(
                    pk=sessions[0].get_decoded()['_auth_user_id'])
            except:
                if request.is_ajax():
                    return HttpResponse("")
                return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap
