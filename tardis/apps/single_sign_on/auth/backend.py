"""Module to implement a custom version of the RemoteUserBackend for the Shibboleth header

"""
import logging

from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import User
from django.http.request import HttpRequest

from tardis.tardis_portal.auth.interfaces import AuthProvider
from tardis.tardis_portal.models.access_control import UserAuthentication

logger = logging.getLogger(__name__)

auth_key = "sso"
auth_display_name = "Single Sign On"


class SSOUserBackend(RemoteUserBackend, AuthProvider):
    """
    Custom implementation of Django's RemoteUserBackend which provides configuration hooks for basic customization.

    Modified from https://github.com/netbox-community/netbox/pull/4299
    """

    @property
    def create_unknown_user(self):
        return settings.REMOTE_AUTH_AUTO_CREATE_USER

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            user = None
        return user

    def configure_user(  # type:ignore
        self,
        request: HttpRequest,
        user: User,
    ) -> User:  # type: ignore
        logger.debug(f"Configure user called with user: {user}")
        try:
            email = request.META[settings.REMOTE_AUTH_EMAIL_HEADER] or None
        except KeyError:
            email = None
        first_name = request.META[settings.REMOTE_AUTH_FIRST_NAME_HEADER]
        surname = request.META[settings.REMOTE_AUTH_SURNAME_HEADER]
        user.first_name = first_name
        user.last_name = surname
        if email:
            user.email = email
        user.save()
        user.userprofile.isDjangoAccount = False  # type: ignore
        user.userprofile.save()  # type: ignore
        try:
            user_auth = UserAuthentication.objects.get(
                userProfile_username=user,
            )
        except UserAuthentication.DoesNotExist:
            user_auth = UserAuthentication(
                userProfile=user.userprofile,  # type: ignore
                username=user.username,
                authMethod=auth_key,
            )
        if user_auth.authMethod != auth_key:
            user_auth.authMethod = auth_key
        user_auth.save()
        return super().configure_user(request, user)
