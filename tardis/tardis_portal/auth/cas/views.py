"""CAS login/logout replacement views"""
from datetime import datetime
from urllib import urlencode
from urlparse import urljoin

from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib import messages
from tardis.tardis_portal.auth.cas.models import PgtIOU

import logging

logger = logging.getLogger(__name__)

__all__ = ['login', 'logout']

def _service_url(request, redirect_to=None):
    """Generates application service URL for CAS"""

    logger.debug("request[%s] redirect_to[%s]" % (request, redirect_to))

    try:
        service = settings.CAS_SERVICE_URL
    except:
        logger.debug("settings.CAS_SERVICE_URL not found! Using request path as service.")
        protocol = ('http://', 'https://')[request.is_secure()]
        host = request.get_host()
        service = protocol + host + request.path

    logger.debug("service = %s" % (service))

    if redirect_to:
        if '?' in service:
            service += '&'
        else:
            service += '?'
        service += urlencode({REDIRECT_FIELD_NAME: redirect_to})
    return service


def _redirect_url(request):
    """Redirects to referring page, or CAS_REDIRECT_URL if no referrer is
    set.
    """
    logger.debug("_redirect_url: request[%s]" % (request))

    if settings.CAS_IGNORE_REDIRECT:
        logger.debug("ignore redirect!")
        return None

    next = request.GET.get(REDIRECT_FIELD_NAME)

    if not next:
        if settings.CAS_IGNORE_REFERER:
            next = settings.CAS_REDIRECT_URL
        else:
            next = request.META.get('HTTP_REFERER', settings.CAS_REDIRECT_URL)

        prefix = (('http://', 'https://')[request.is_secure()] +
                  request.get_host())
        if next.startswith(prefix):
            next = next[len(prefix):]

    return next


def _login_url(service, ticket='ST'):
    """Generates CAS login URL"""

    logger.debug("service[%s] ticket[%s]" % (service, ticket))

    LOGINS = {'ST':'login',
              'PT':'proxyValidate'}
    params = {'service': service}
    if settings.CAS_EXTRA_LOGIN_PARAMS:
        params.update(settings.CAS_EXTRA_LOGIN_PARAMS)
    if not ticket:
        ticket = 'ST'
    login = LOGINS.get(ticket[:2], 'login')
    return urljoin(settings.CAS_SERVER_URL, login) + '?' + urlencode(params)


def _logout_url(request, next_page=None):
    """Generates CAS logout URL"""

    logger.debug("request[%s] next_page[%s]" % (request, next_page))

    url = urljoin(settings.CAS_SERVER_URL, 'logout')

    if next_page:
        protocol = ('http://', 'https://')[request.is_secure()]
        host = request.get_host()
        url += '?' + urlencode({'service': protocol + host + next_page})

    return url


def login(request, next_page=None, required=False):
    """Forwards to CAS login URL or verifies CAS ticket"""

    logger.debug("request[%s] next_page[%s] required[%s]" % (request, next_page, required))

    if not next_page:
        next_page = _redirect_url(request)
    if request.user.is_authenticated():
        #message = "You are logged in as %s." % request.user.username
        #request.user.message_set.create(message=message)
        return HttpResponseRedirect(next_page)
    ticket = request.GET.get('ticket')
    service = _service_url(request, next_page)
    if ticket:
        logger.debug("auth.authenticate(ticket[%s], service[%s])" % (ticket, service))
        user = auth.authenticate(ticket=ticket, service=service)

        if user is not None:
            auth.login(request, user)
            #name = user.first_name or user.username
            #message = "Login succeeded. Welcome, %s." % name
            #user.message_set.create(message=message)
            return HttpResponseRedirect(next_page)
        elif settings.CAS_RETRY_LOGIN or required:
            return HttpResponseRedirect(_login_url(service, ticket))
        else:
            #error = "<h1>Forbidden</h1><p>Login failed.</p>"
            #return HttpResponseForbidden(error)
            messages.error(request, "Login failed!")
            return HttpResponseRedirect(next_page)
    else:
        return HttpResponseRedirect(_login_url(service, ticket))


def logout(request, next_page=None):
    """Redirects to CAS logout page"""

    logger.debug("request[%s] next_page[%s]" % (request, next_page))

    from django.contrib.auth import logout
    logout(request)
    if not next_page:
        next_page = _redirect_url(request)
    if settings.CAS_LOGOUT_COMPLETELY:
        return HttpResponseRedirect(_logout_url(request, next_page))
    else:
        messages.error(request, 'Please close the browser to complete logout!')
        return HttpResponseRedirect(next_page)

def proxy_callback(request):
    """Handles CAS 2.0+ XML-based proxy callback call.
    Stores the proxy granting ticket in the database for
    future use.

    NB: Use created and set it in python in case database
    has issues with setting up the default timestamp value
    """

    logger.debug("request[%s]" % (request))

    pgtIou = request.GET.get('pgtIou')
    tgt = request.GET.get('pgtId')

    if not (pgtIou and tgt):
        return HttpResponse()

    try:
        PgtIOU.objects.create(tgt=tgt, pgtIou=pgtIou, created=datetime.now())
    except:
        return HttpResponse('PGT storage failed for %s' % str(request.GET), mimetype="text/plain")

    return HttpResponse('Success', mimetype="text/plain")

