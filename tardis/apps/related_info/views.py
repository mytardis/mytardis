import json

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template import Context

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.models import \
    Experiment, ExperimentParameterSet, Schema
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager
from tardis.tardis_portal.shortcuts import render_response_index, \
    return_response_error, return_response_not_found

from .forms import RelatedInfoForm

SCHEMA_URI = 'http://ands.org.au/standards/rif-cs/registryObjects#relatedInfo'
PARAMETER_NAMES = ['type','identifier','title','notes']

def _get_dict_from_ps(ps):
    '''
    Build dictionary by getting the parameter values from the keys, then
    zipping it all together.
    '''
    psm = ParameterSetManager(ps)
    return dict([('id', ps.id)]+ # Use set ID
                zip(PARAMETER_NAMES,
                    (psm.get_param(k, True) for k in PARAMETER_NAMES)))

def _get_schema():
    try:
        return Schema.objects.get(namespace=SCHEMA_URI)
    except Schema.DoesNotExist:
        from django.core.management import call_command
        call_command('loaddata', 'related_info_schema')
        return _get_schema()


@authz.experiment_access_required
def index(request, experiment_id):
    try:
        experiment = Experiment.safe.get(request, experiment_id)
    except PermissionDenied:
        return return_response_error(request)
    except Experiment.DoesNotExist:
        return return_response_not_found(request)

    c = Context({'experiment': experiment, 'form': RelatedInfoForm()})
    return HttpResponse(render_response_index(request,
                        'related_info/index.html', c))


def list_or_create_related_info(request, *args, **kwargs):
    if request.method == 'POST':
        return _create_related_info(request, *args, **kwargs)
    else:
        return _list_related_info(request, *args, **kwargs)


def get_or_update_or_delete_related_info(request, *args, **kwargs):
    if request.method == 'PUT':
        return _update_related_info(request, *args, **kwargs)
    elif request.method == 'DELETE':
        return _delete_related_info(request, *args, **kwargs)
    else:
        return _get_related_info(request, *args, **kwargs)


def _list_related_info(request, experiment_id):
    if not authz.has_experiment_access(request, experiment_id):
        return return_response_error(request)
    sets = ExperimentParameterSet.objects.filter(schema__namespace=SCHEMA_URI)
    return HttpResponse(json.dumps([_get_dict_from_ps(ps)
                                    for ps in sets]),
                        content_type='application/json; charset=utf-8')


def _get_related_info(request, experiment_id, related_info_id):
    if not authz.has_experiment_access(request, experiment_id):
        return return_response_error(request)
    try:
        ps = ExperimentParameterSet.objects.get(schema__namespace=SCHEMA_URI,
                                            id=related_info_id)
        return HttpResponse(json.dumps(_get_dict_from_ps(ps)),
                            content_type='application/json; charset=utf-8')
    except:
        return return_response_not_found(request)


def _create_related_info(request, experiment_id):
    if not authz.has_write_permissions(request, experiment_id):
        return return_response_error(request)
    form = RelatedInfoForm(json.loads(request.body))
    if not form.is_valid():
        return HttpResponse('', status=400)
    ps = ExperimentParameterSet(experiment_id=experiment_id,
                                schema=_get_schema())
    ps.save()
    ParameterSetManager(ps).set_params_from_dict(form.cleaned_data)
    return HttpResponse(json.dumps(_get_dict_from_ps(ps)),
                        content_type='application/json; charset=utf-8',
                        status=201)


def _update_related_info(request, experiment_id, related_info_id):
    if not authz.has_write_permissions(request, experiment_id):
        return return_response_error(request)

    form = RelatedInfoForm(json.loads(request.body))
    if not form.is_valid():
        return HttpResponse('', status=400)

    try:
        ps = ExperimentParameterSet.objects.get(experiment_id=experiment_id,
                                                id=related_info_id)
    except ExperimentParameterSet.DoesNotExist:
        return HttpResponse('', status=404)

    ParameterSetManager(ps).set_params_from_dict(form.cleaned_data)
    return HttpResponse(json.dumps(_get_dict_from_ps(ps)),
                        content_type='application/json; charset=utf-8',
                        status=201)


def _delete_related_info(request, experiment_id, related_info_id):
    if not authz.has_write_permissions(request, experiment_id):
        return return_response_error(request)

    try:
        ps = ExperimentParameterSet.objects.get(experiment_id=experiment_id,
                                                id=related_info_id)
    except ExperimentParameterSet.DoesNotExist:
        return HttpResponse('', status=404)
    obj = _get_dict_from_ps(ps)
    ps.delete()
    return HttpResponse(json.dumps(obj),
                        content_type='application/json; charset=utf-8')