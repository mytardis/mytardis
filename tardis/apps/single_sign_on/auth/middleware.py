"""Shibboleth Header Authentication Module

.. moduleauthor:: Chris Seal <c.seal@auckland.ac.nz>

This module provides an authentication middleware for Shibboleth based authentication
where the authentication has been offloaded to a dedicated auth service. In this case
a header in injected into the request from the IDP will include the username"""

import logging

from django.conf import settings
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib.sessions.backends.db import SessionStore

logger = logging.getLogger(__name__)


class SSOUserMiddleware(RemoteUserMiddleware):
    """
    Custom implementation of Django's RemoteUserMiddleware which allows for a user-configurable HTTP header name.

    Modified from https://github.com/netbox-community/netbox/pull/4299
    """

    force_logout_if_no_header = False

    @property
    def header(self):
        return settings.REMOTE_AUTH_HEADER

    def process_request(self, request):
        if not settings.REMOTE_AUTH_ENABLED:
            return

        # Flush expired sessions
        SessionStore.clear_expired()
        super().process_request(request)
