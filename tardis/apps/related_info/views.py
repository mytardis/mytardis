import json

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template import Context

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.models import \
    Experiment, ExperimentParameterSet
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager
from tardis.tardis_portal.shortcuts import render_response_index, \
    return_response_error, return_response_not_found

SCHEMA_URI = 'http://ands.org.au/standards/rif-cs/registryObjects#relatedInfo'
PARAMETER_NAMES = ['type','identifier','title','notes']

def _get_dict_from_set(ps):
    '''
    Build dictionary by getting the parameter values from the keys, then
    zipping it all together.
    '''
    psm = ParameterSetManager(ps)
    return dict([('id', ps.id)]+ # Use set ID
                zip(PARAMETER_NAMES,
                    (psm.get_param(k, True) for k in PARAMETER_NAMES)))

@authz.experiment_access_required
def index(request, experiment_id):
    try:
        experiment = Experiment.safe.get(request, experiment_id)
    except PermissionDenied:
        return return_response_error(request)
    except Experiment.DoesNotExist:
        return return_response_not_found(request)

    c = Context({'experiment': experiment})
    return HttpResponse(render_response_index(request,
                        'related_info/index.html', c))

@authz.experiment_access_required
def list_related_info(request, experiment_id):
    sets = ExperimentParameterSet.objects.filter(schema__namespace=SCHEMA_URI)
    return HttpResponse(json.dumps([_get_dict_from_set(ps)
                                    for ps in sets]),
                        content_type='application/json; charset=utf-8')

@authz.experiment_access_required
def get_related_info(request, experiment_id, related_info_id):
    try:
        ps = ExperimentParameterSet.objects.get(schema__namespace=SCHEMA_URI,
                                            id=related_info_id)
        return HttpResponse(json.dumps(_get_dict_from_set(ps)),
                            content_type='application/json; charset=utf-8')
    except:
        return return_response_not_found(request)

@authz.experiment_ownership_required
def create_related_info(request, experiment_id):
    pass

@authz.experiment_ownership_required
def update_related_info(request, experiment_id, related_info_id):
    pass

@authz.experiment_ownership_required
def delete_related_info(request, experiment_id, related_info_id):
    pass