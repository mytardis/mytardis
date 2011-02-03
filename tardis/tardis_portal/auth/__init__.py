# -*- coding: utf-8 -*-
from tardis.tardis_portal.auth.AuthService import AuthService

GROUPS = "_group_list"


auth_service = AuthService()


def login(request, user):
    from django.contrib.auth import login
    login(request, user)
    request.__class__.groups = auth_service.getGroups(request)
    request.session[GROUPS] = request.groups


class LazyGroups(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_groups'):
            if GROUPS in request.session:
                return request.session[GROUPS]
            request._cached_groups = auth_service.getGroups(request)
        return request._cached_groups


class AuthorizationMiddleware(object):
    def process_request(self, request):
        assert hasattr(request, 'session'), "The Django authorization middleware requires session middleware to be installed. Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.sessions.middleware.SessionMiddleware'."
        request.__class__.groups = LazyGroups()
        return None
