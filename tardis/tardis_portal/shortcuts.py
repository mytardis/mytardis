import json, cgi, re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.template import RequestContext, Context
from django.http import HttpResponse, \
    HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError

from tardis.tardis_portal.models import \
    ExperimentParameterSet, Schema
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager

from django.template.loader import render_to_string
from django.contrib.sites.models import Site

def render_response_index(request, *args, **kwargs):
    return render(request, *args, **kwargs)


def render_response_search(request, url, c):

    from tardis.tardis_portal.views import getNewSearchDatafileSelectionForm

    links = {}
    for app in settings.INSTALLED_APPS:
        if app.startswith('tardis.apps.'):
            view = '%s.views.search' % app
            try:
                links[app.split('.')[2]] = reverse(view)
            except:
                pass

    c['searchDatafileSelectionForm'] = \
        getNewSearchDatafileSelectionForm(request.GET.get('type', None))
    c['links'] = links

    return render(request, url, c)


def render_error_message(request, message, status=400):
    """Render a simple text error message in a generic error page.  Any newlines are turned into <br>."""
    formatted = cgi.escape(message).replace('\n', '<br/>')
    return render(request, 'tardis_portal/user_error.html',
                  {'error_message' : formatted}, status=status)


def return_response_not_found(request):
    return HttpResponseNotFound(render_response_index(request, '404.html', {}))


def return_response_error_message(request, redirect_path, context):
    return HttpResponseServerError(render_response_index(request,
                                   redirect_path, context))


def return_response_error(request):
    return HttpResponseForbidden(render_response_index(request, '403.html', {}))


def get_experiment_referer(request, dataset_id):
    from tardis.tardis_portal.auth.decorators import get_accessible_experiments_for_dataset

    try:
        from_url = request.META['HTTP_REFERER']
        from_url_split = re.sub('^https?:\/\/', '', from_url).split('/')

        domain_url_split = Site.objects.get_current().domain.split('//')

        referer = 0
        if not from_url_split[0] == domain_url_split[1]:
            return None

        if from_url_split[1] == 'experiment' and from_url_split[2] == 'view':
            referer = int(from_url_split[3])
        else:
            return None

        for experiment in get_accessible_experiments_for_dataset(request, dataset_id):
            if experiment.id == referer:
                return experiment
    except:
        pass


def render_to_file(template, filename, context):
    string_for_output = render_to_string(template, context)
    # The render_to_string method returns a unicode string, which will cause
    # an error when written to file if the string contain diacritics. We
    # need to do a utf-8 encoding before writing to file
    # see http://packages.python.org/kitchen/unicode-frustrations.html
    open(filename, "w").write(string_for_output.encode('utf8', 'replace'))



class RestfulExperimentParameterSet:
    '''
    Helper class which enables a Backbone.sync-compatible interface to be
    created for a ExperimentParameterSet just by specifying a function which
    provides the schema and a form.

    (A function for the schema is required rather than the actual schema, as
    to run unit tests effectively the object needs to be able to create the
    schema after instantiation.)

    For UI consistency, it's best to make sure the schema has hidden == true.
    '''

    def __init__(self, schema_func, form_cls):
        '''
        Takes a schema URI and a Form class.
        '''
        self.schema_func = schema_func
        self.form_cls = form_cls
        self.parameter_names = form_cls().fields.keys()

    def _get_schema(self):
        ''' Use schema function to get the schema. '''
        return self.schema_func()
    schema = property(_get_schema)

    def __str__(self):
        return "%s for %s into %s" % \
            (self.__class__, self.form_cls, self.schema.namespace)

    def _get_dict_from_ps(self, ps):
        '''
        Build dictionary by getting the parameter values from the keys, then
        zipping it all together.
        '''
        psm = ParameterSetManager(ps)
        return dict([('id', ps.id)]+ # Use set ID
                    zip(self.parameter_names,
                        (psm.get_param(k, True) for k in self.parameter_names)))

    def _get_view_functions(self):
        context = self

        # Collection resource
        def list_or_create(request, *args, **kwargs):
            if request.method == 'POST':
                return context._create(request, *args, **kwargs)
            else:
                return context._list(request, *args, **kwargs)
        # Item resource
        def get_or_update_or_delete(request, *args, **kwargs):
            if request.method == 'PUT':
                return context._update(request, *args, **kwargs)
            elif request.method == 'DELETE':
                return context._delete(request, *args, **kwargs)
            else:
                return context._get(request, *args, **kwargs)

        return {'list_or_create': list_or_create,
                'get_or_update_or_delete': get_or_update_or_delete }

    view_functions = property(_get_view_functions)

    def _list(self, request, experiment_id):
        from tardis.tardis_portal.auth.decorators import has_experiment_access
        if not has_experiment_access(request, experiment_id):
            return return_response_error(request)
        sets = ExperimentParameterSet.objects.filter(schema=self.schema,
                                                     experiment__pk=experiment_id)
        return HttpResponse(json.dumps([self._get_dict_from_ps(ps)
                                        for ps in sets]),
                            content_type='application/json; charset=utf-8')


    def _get(self, request, experiment_id, ps_id):
        from tardis.tardis_portal.auth.decorators import has_experiment_access
        if not has_experiment_access(request, experiment_id):
            return return_response_error(request)
        try:
            ps = ExperimentParameterSet.objects.get(schema=self.schema,
                                                    experiment__pk=experiment_id,
                                                    id=ps_id)
            return HttpResponse(json.dumps(self._get_dict_from_ps(ps)),
                                content_type='application/json; charset=utf-8')
        except:
            return return_response_not_found(request)


    def _create(self, request, experiment_id):
        from tardis.tardis_portal.auth.decorators import has_experiment_write
        if not has_experiment_write(request, experiment_id):
            return return_response_error(request)
        form = self.form_cls(json.loads(request.body))
        if not form.is_valid():
            return HttpResponse('', status=400)
        ps = ExperimentParameterSet(experiment_id=experiment_id,
                                    schema=self.schema)
        ps.save()
        ParameterSetManager(ps).set_params_from_dict(form.cleaned_data)
        return HttpResponse(json.dumps(self._get_dict_from_ps(ps)),
                            content_type='application/json; charset=utf-8',
                            status=201)


    def _update(self, request, experiment_id, ps_id):
        from tardis.tardis_portal.auth.decorators import has_experiment_write
        if not has_experiment_write(request, experiment_id):
            return return_response_error(request)

        form = self.form_cls(json.loads(request.body))
        if not form.is_valid():
            return HttpResponse('', status=400)

        try:
            ps = ExperimentParameterSet.objects.get(experiment_id=experiment_id,
                                                    id=ps_id)
        except ExperimentParameterSet.DoesNotExist:
            return HttpResponse('', status=404)

        ParameterSetManager(ps).set_params_from_dict(form.cleaned_data)
        return HttpResponse(json.dumps(self._get_dict_from_ps(ps)),
                            content_type='application/json; charset=utf-8',
                            status=201)


    def _delete(self, request, experiment_id, ps_id):
        from tardis.tardis_portal.auth.decorators import has_experiment_write
        if not has_experiment_write(request, experiment_id):
            return return_response_error(request)

        try:
            ps = ExperimentParameterSet.objects.get(experiment_id=experiment_id,
                                                    id=ps_id)
        except ExperimentParameterSet.DoesNotExist:
            return HttpResponse('', status=404)
        print (ps.schema_id, self.schema.id, str(self))
        obj = self._get_dict_from_ps(ps)
        ps.delete()
        return HttpResponse(json.dumps(obj),
                            content_type='application/json; charset=utf-8')
