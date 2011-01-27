from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.db.models import Q

from tardis.tardis_portal.models import Experiment, Dataset_File, GroupAdmin
from tardis.tardis_portal.shortcuts import *


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
