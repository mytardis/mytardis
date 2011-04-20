from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext, Context
from django.http import HttpResponseForbidden, HttpResponseNotFound, \
    HttpResponseServerError


def render_response_index(request, *args, **kwargs):

    is_authenticated = request.user.is_authenticated()
    if is_authenticated:
        is_superuser = request.user.is_superuser
        username = request.user.username
    else:
        is_superuser = False
        username = None

    kwargs['context_instance'] = RequestContext(request)
    kwargs['context_instance']['is_authenticated'] = is_authenticated
    kwargs['context_instance']['is_superuser'] = is_superuser
    kwargs['context_instance']['username'] = username

    if request.mobile:
        template_path = args[0]
        split = template_path.partition('/')
        args = (split[0] + '/mobile/' + split[2], ) + args[1:]

    return render_to_response(*args, **kwargs)


def render_response_search(request, *args, **kwargs):

    from tardis.tardis_portal.views import getNewSearchDatafileSelectionForm

    is_authenticated = request.user.is_authenticated()
    if is_authenticated:
        is_superuser = request.user.is_superuser
        username = request.user.username
    else:
        is_superuser = False
        username = None


    links = {}
    for app in settings.INSTALLED_APPS:
        if app.startswith('tardis.apps.'):
            view = '%s.views.search' % app
            try:
                links[app.split('.')[2]] = reverse(view)
            except:
                pass

    kwargs['context_instance'] = RequestContext(request)
    kwargs['context_instance']['is_authenticated'] = is_authenticated
    kwargs['context_instance']['is_superuser'] = is_superuser
    kwargs['context_instance']['username'] = username
    kwargs['context_instance']['searchDatafileSelectionForm'] = \
        getNewSearchDatafileSelectionForm(request.GET.get('type', None))
    kwargs['context_instance']['links'] = links

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
