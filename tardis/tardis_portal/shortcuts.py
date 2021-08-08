# pylint: disable=http-response-with-json-dumps,http-response-with-content-type-json
import json
import re
from html import escape

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.contrib.sites.models import Site

from .models import ExperimentParameterSet
from .ParameterSetManager import ParameterSetManager


def render_response_index(request, *args, **kwargs):
    return render(request, *args, **kwargs)


def render_error_message(request, message, status=400):
    """
    Render a simple text error message in a generic error page.
    Any newlines are turned into <br>.
    """
    formatted = escape(message).replace('\n', '<br/>')
    return render(request, 'tardis_portal/user_error.html',
                  {'error_message': formatted}, status=status)


def return_response_not_found(request):
    return render_response_index(request, '404.html', {}, status=404)


def return_response_error_message(request, redirect_path, context):
    return render_response_index(request, redirect_path, context, status=500)


def return_response_error(request):
    return render_response_index(request, '403.html', {}, status=403)


def redirect_back_with_error(request, message):
    root_url = "{0}://{1}/".format(request.scheme, request.get_host())
    redirect_url = request.META.get("HTTP_REFERER", root_url)
    if root_url not in redirect_url:
        redirect_url = root_url
    return HttpResponseRedirect(redirect_url + "#error:" + message)


def get_experiment_referer(request, dataset_id):
    from .auth.decorators import get_accessible_experiments_for_dataset

    try:
        from_url = request.META['HTTP_REFERER']
        from_url_split = re.sub('^https?:\/\/', '', from_url).split('/')

        domain_url_split = Site.objects.get_current().domain.split('//')

        referer = 0
        if from_url_split[0] != domain_url_split[1]:
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

    return None


def render_to_file(template, filename, context):
    '''Write the output of render_to_string to a file.

    The :func:`~django.template.loader.render_to_string`
    method returns a unicode string, which can be written
    to a file with ``locale.getpreferredencoding()``,
    usually UTF-8.
    '''
    string_for_output = render_to_string(template, context)
    with open(filename, 'w') as output_file:
        output_file.write(string_for_output)


class RestfulExperimentParameterSet(object):
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
                    list(zip(self.parameter_names,
                         (psm.get_param(k, True) for k in self.parameter_names))))

    def _get_view_functions(self):
        context = self

        # Collection resource
        def list_or_create(request, *args, **kwargs):
            if request.method == 'POST':
                return context._create(request, *args, **kwargs)
            return context._list(request, *args, **kwargs)

        # Item resource
        def get_or_update_or_delete(request, *args, **kwargs):
            if request.method == 'PUT':
                return context._update(request, *args, **kwargs)
            if request.method == 'DELETE':
                return context._delete(request, *args, **kwargs)
            return context._get(request, *args, **kwargs)

        return {'list_or_create': list_or_create,
                'get_or_update_or_delete': get_or_update_or_delete }

    view_functions = property(_get_view_functions)

    def _list(self, request, experiment_id):
        from .auth.decorators import has_experiment_access
        if not has_experiment_access(request, experiment_id):
            return return_response_error(request)
        sets = ExperimentParameterSet.objects.filter(schema=self.schema,
                                                     experiment__pk=experiment_id)
        return HttpResponse(json.dumps([self._get_dict_from_ps(ps)
                                        for ps in sets]),
                            content_type='application/json; charset=utf-8')


    def _get(self, request, experiment_id, ps_id):
        from .auth.decorators import has_experiment_access
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
        from .auth.decorators import has_experiment_write
        if not has_experiment_write(request, experiment_id):
            return return_response_error(request)
        form = self.form_cls(json.loads(request.body.decode()))
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
        from .auth.decorators import has_experiment_write
        if not has_experiment_write(request, experiment_id):
            return return_response_error(request)

        form = self.form_cls(json.loads(request.body.decode()))
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
        from .auth.decorators import has_experiment_write
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
