from django.shortcuts import render_to_response
from django.template import RequestContext, Context

from django.http import HttpResponseForbidden, HttpResponseNotFound, \
    HttpResponseServerError


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


def return_response_not_found(request):
    c = Context({'status': 'ERROR: Not Found', 'error': True})
    return HttpResponseNotFound(render_response_index(request,
                                'tardis_portal/blank_status.html', c))


def return_response_error_message(request, redirect_path, context):
    return HttpResponseServerError(render_response_index(request,
                                   redirect_path, context))


def return_response_error(request):
    c = Context({'status': 'ERROR: Forbidden', 'error': True})
    return HttpResponseForbidden(render_response_index(request,
                                 'tardis_portal/blank_status.html', c))
