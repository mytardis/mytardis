"""CAS authentication middleware"""

from urllib import urlencode

from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import login, logout
from django.core.urlresolvers import reverse
from django.conf import settings

from tardis.tardis_portal.auth.cas.views import login as cas_login, logout as cas_logout, _service_url

__all__ = ['CASMiddleware']

class CASMiddleware(object):
    """Middleware that allows CAS authentication on admin pages"""

    def process_request(self, request):
        """Logs in the user if a ticket is append as parameter"""

        if settings.CAS_ENABLED:
            request.session['use_cas'] = settings.CAS_ENABLED
        else:
            request.session['use_cas'] = False

        ticket = request.GET.get('ticket')
        # fix for tastypie
        request._read_started = False

        if ticket:
            from django.contrib import auth
            user = auth.authenticate(ticket=ticket, service=_service_url(request))
            if user is not None:
                auth.login(request, user)




    def process_view(self, request, view_func, view_args, view_kwargs):
        """Forwards unauthenticated requests to the admin page to the CAS
        login URL, as well as calls to django.contrib.auth.views.login and
        logout.
        """

        if view_func == login:
            return cas_login(request, *view_args, **view_kwargs)
        elif view_func == logout:
            return cas_logout(request, *view_args, **view_kwargs)

        if settings.CAS_ADMIN_PREFIX:
            if not request.path.startswith(settings.CAS_ADMIN_PREFIX):
                return None
        elif not view_func.__module__.startswith('django.contrib.admin.'):
            return None

        if request.user.is_authenticated():
            if request.user.is_staff:
                return None
            else:
                error = ('<h1>Forbidden</h1><p>You do not have staff '
                         'privileges.</p>')
                return HttpResponseForbidden(error)
        params = urlencode({REDIRECT_FIELD_NAME: request.get_full_path()})
        return HttpResponseRedirect(reverse(cas_login) + '?' + params)
