"""Module to implement a custom version of the RemoteUserBackend for the Shibboleth header

"""
import logging

from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import User
from django.http.request import HttpRequest

from tardis.apps.identifiers.models import UserPID
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

    def authenticate(self, request, remote_user):
        """
        The username passed as ``remote_user`` is considered trusted. Return
        the ``User`` object with the given username. Create a new ``User``
        object if ``create_unknown_user`` is ``True``.

        Return None if ``create_unknown_user`` is ``False`` and a ``User``
        object with the given username is not found in the database.
        """
        if not remote_user:
            return None
        user = None
        username = self.clean_username(remote_user)

        # Note that this could be accomplished in one try-except clause, but
        # instead we use get_or_create when creating unknown users since it has
        # built-in safeguards for multiple threads.
        if self.create_unknown_user:
            user, _ = User.objects.get_or_create(
                username=username
            )
        else:
            try:
                user = User.objects.get_by_natural_key(username)
            except User.DoesNotExist:
                return None
        user = self.configure_user(request, user)
        return user if self.user_can_authenticate(user) else None

    def configure_user(  # type:ignore
        self,
        request: HttpRequest,
        user: User,
    ) -> User:  # type: ignore
        try:
            email = request.META[settings.REMOTE_AUTH_EMAIL_HEADER] or None
        except KeyError:
            email = None
        first_name = request.META[settings.REMOTE_AUTH_FIRST_NAME_HEADER]
        surname = request.META[settings.REMOTE_AUTH_SURNAME_HEADER]
        orcid = None
        if "identifiers" in settings.INSTALLED_APPS and "user" in settings.OBJECTS_WITH_IDENTIFIERS:
            orcid = request.META[settings.REMOTE_AUTH_ORCID_HEADER] or None
        updated_flag = False
        if user.first_name != first_name:
            user.first_name = first_name
            updated_flag = True
        if user.last_name != surname:
            user.last_name = surname
            updated_flag = True
        if email and user.email != email:
            user.email = email
            updated_flag = True
        if orcid:
            identifiers = [*UserPID.objects.all(user=user).values_list("identifier", flat=True)]
            if orcid not in identifiers:
                identifier = UserPID.objects.create(user=user, identifier=orcid)
                identifier.save()
        if updated_flag:
            user.save()
        if user.userprofile.isDjangoAccount: #type: ignore
            user.userprofile.isDjangoAccount = False  # type: ignore
            user.userprofile.save()  # type: ignore
        try:
            user_auth = UserAuthentication.objects.get(
                username=user,
            )
        except UserAuthentication.DoesNotExist:
            user_auth = UserAuthentication(
                userProfile=user.userprofile,  # type: ignore
                username=user.username,
                authenticationMethod=auth_key,
            )
        if user_auth.authenticationMethod != auth_key:
            user_auth.authenticationMethod = auth_key
            user_auth.save()
        return super().configure_user(request, user)
