from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.template import RequestContext, Context
from django.http import HttpResponseForbidden, HttpResponseNotFound, \
    HttpResponseServerError
from tardis.tardis_portal.staging import get_full_staging_path
from django.template.loader import render_to_string


def render_response_index(request, *args, **kwargs):

    is_authenticated = request.user.is_authenticated()
    if is_authenticated:
        is_superuser = request.user.is_superuser
        username = request.user.username
    else:
        is_superuser = False
        username = None

    if ('context_instance' in kwargs):
        kwargs['context_instance'] = RequestContext(request,
                                                    kwargs['context_instance'])
    else:
        kwargs['context_instance'] = RequestContext(request)
    kwargs['context_instance']['is_authenticated'] = is_authenticated
    kwargs['context_instance']['is_superuser'] = is_superuser
    kwargs['context_instance']['username'] = username

    staging = get_full_staging_path(
                                username)
    if staging:
        kwargs['context_instance']['has_staging_access'] = True
    else:
        kwargs['context_instance']['has_staging_access'] = False

    return render(request, *args, **kwargs)


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

    staging = get_full_staging_path(
                                username)
    if staging:
        kwargs['context_instance']['has_staging_access'] = True
    else:
        kwargs['context_instance']['has_staging_access'] = False

    return render(request, *args, **kwargs)


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

def render_to_file(template, filename, context):
    string_for_output = render_to_string(template, context)
    # The render_to_string method returns a unicode string, which will cause
    # an error when written to file if the string contain diacritics. We
    # need to do a utf-8 encoding before writing to file
    # see http://packages.python.org/kitchen/unicode-frustrations.html
    open(filename, "w").write(string_for_output.encode('utf8', 'replace'))
