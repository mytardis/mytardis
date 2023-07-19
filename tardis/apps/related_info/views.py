from django.core.exceptions import PermissionDenied

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.models import Experiment, Schema
from tardis.tardis_portal.shortcuts import (
    RestfulExperimentParameterSet,
    render_response_index,
    return_response_error,
    return_response_not_found,
)

from .forms import RelatedInfoForm

SCHEMA_URI = 'http://ands.org.au/standards/rif-cs/registryObjects#relatedInfo'
PARAMETER_NAMES = RelatedInfoForm().fields.keys()


def _get_schema_func(schema_uri):
    def get_schema():
        try:
            return Schema.objects.get(namespace=schema_uri)
        except Schema.DoesNotExist:
            from django.core.management import call_command
            call_command('loaddata', 'related_info_schema')
            return get_schema()
    return get_schema


@authz.experiment_access_required
def index(request, experiment_id):
    try:
        experiment = Experiment.safe.get(request.user, experiment_id)
    except PermissionDenied:
        return return_response_error(request)
    except Experiment.DoesNotExist:
        return return_response_not_found(request)

    c = {'experiment': experiment}

    if authz.has_write(request, experiment_id, "experiment"):
        template = 'related_info/index.html'
    else:
        template = 'related_info/index_ro.html'
    return render_response_index(request, template, c)


# Create an object which handles our requests
handlerObj = RestfulExperimentParameterSet(_get_schema_func(SCHEMA_URI),
                                           RelatedInfoForm)
# Bind the handlers it provides to scope
list_or_create_related_info = \
    handlerObj.view_functions['list_or_create']
get_or_update_or_delete_related_info = \
    handlerObj.view_functions['get_or_update_or_delete']
