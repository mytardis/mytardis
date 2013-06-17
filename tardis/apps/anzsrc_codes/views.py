import json

from rdflib import plugin, URIRef
from rdflib.graph import Graph
from rdflib.parser import Parser

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template import Context

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.models import \
    Experiment, Schema
from tardis.tardis_portal.shortcuts import render_response_index, \
    return_response_error, return_response_not_found, \
    RestfulExperimentParameterSet

from .forms import FoRCodeForm

SCHEMA_URI = 'http://purl.org/asc/1297.0/2008/for/'
PARAMETER_NAMES = FoRCodeForm().fields.keys()

plugin.register('application/octet-stream', Parser,
     'rdflib.plugins.parsers.notation3', 'N3Parser')

for_graph = Graph()
for_graph.parse(SCHEMA_URI)

def _get_schema_func(schema_uri):
    def get_schema():
        try:
            return Schema.objects.get(namespace=schema_uri)
        except Schema.DoesNotExist:
            from django.core.management import call_command
            call_command('loaddata', 'anzsrc_for_schema')
            return get_schema()
    return get_schema

def _get_for_codes():
    codeTerm = URIRef("http://purl.org/asc/1297.0/code")
    narrowerTerm = URIRef("http://www.w3.org/2004/02/skos/core#narrower")

    def get_narrower(subject):
        return [ obj.toPython()
                for obj in for_graph.objects(subject=subject,
                                             predicate=narrowerTerm)]

    def get_option(subject, object_):
        return { 'uri': subject.toPython(),
                 'name': for_graph.label(subject).toPython(),
                 'code': object_.toPython(),
                 'narrower': get_narrower(subject) }

    return sorted([ get_option(subject, object_) for subject, object_
                    in for_graph.subject_objects(predicate=codeTerm) ],
                  key=lambda d: d['code'])

# Create an object which handles our requests
handlerObj = RestfulExperimentParameterSet(_get_schema_func(SCHEMA_URI),
                                           FoRCodeForm)
# Bind the handlers it provides to scope
list_or_create_for_code = \
    handlerObj.view_functions['list_or_create']
get_or_update_or_delete_for_code = \
    handlerObj.view_functions['get_or_update_or_delete']

@authz.experiment_access_required
def index(request, experiment_id):
    try:
        experiment = Experiment.safe.get(request.user, experiment_id)
    except PermissionDenied:
        return return_response_error(request)
    except Experiment.DoesNotExist:
        return return_response_not_found(request)

    c = Context({'experiment': experiment,
                 'for_code_json': json.dumps(_get_for_codes(),
                                             sort_keys=True)})

    if authz.has_write_permissions(request, experiment_id):
        template = 'anzsrc_codes/index.html'
    else:
        template = 'anzsrc_codes/index_ro.html'
    return HttpResponse(render_response_index(request, template, c))
