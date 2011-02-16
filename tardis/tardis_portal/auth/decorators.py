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
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.db.models import Q

from tardis.tardis_portal.models import Experiment, Dataset_File, GroupAdmin
from tardis.tardis_portal.shortcuts import return_response_error


def get_accessible_experiments(request):

    experiments = Experiment.safe.all(request)
    return experiments


def get_accessible_datafiles_for_user(request):

    experiments = get_accessible_experiments(request)
    if experiments.count() == 0:
        return []

    queries = [Q(dataset__experiment__id=e.id) for e in experiments]

    query = queries.pop()
    for item in queries:
        query |= item

    return Dataset_File.objects.filter(query)


def has_experiment_ownership(request, experiment_id):

    experiment = Experiment.safe.owned(request).filter(
        pk=experiment_id)
    if experiment:
        return True
    return False


def has_experiment_access(request, experiment_id):

    try:
        Experiment.safe.get(request, experiment_id)
        return True
    except PermissionDenied:
        return False


def has_dataset_access(request, dataset_id):

    experiment = Experiment.objects.get(dataset__pk=dataset_id)
    if has_experiment_access(request, experiment.id):
        return True
    else:
        return False


def has_datafile_access(request, dataset_file_id):

    experiment = Experiment.objects.get(dataset__dataset_file=dataset_file_id)
    if has_experiment_access(request, experiment.id):
        return True
    else:
        return False


@login_required
def is_group_admin(request, group_id):

    groupadmin = GroupAdmin.objects.filter(user=request.user,
                                           group__id=group_id)
    if groupadmin.count():
        return True
    else:
        return False


def group_ownership_required(f):

    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect('/login?next=%s' % request.path)
        if not is_group_admin(request, kwargs['group_id']):
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def experiment_ownership_required(f):

    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect('/login?next=%s' % request.path)
        if not has_experiment_ownership(request, kwargs['experiment_id']):
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def experiment_access_required(f):

    def wrap(request, *args, **kwargs):
        if not has_experiment_access(request, kwargs['experiment_id']):
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def dataset_access_required(f):

    def wrap(request, *args, **kwargs):
        if not has_dataset_access(request, kwargs['dataset_id']):
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def datafile_access_required(f):

    def wrap(request, *args, **kwargs):

        if not has_datafile_access(request, kwargs['dataset_file_id']):
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap
