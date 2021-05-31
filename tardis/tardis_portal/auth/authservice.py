# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2011, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""
models.py

.. moduleauthor:: Gerson Galang <gerson.galang@versi.edu.au>
.. moduleauthor:: Russell Sim <russell.sim@monash.edu>

"""
from functools import cmp_to_key
import logging
from importlib import import_module

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission

from ..auth.localdb_auth import auth_key as localdb_auth_key
from ..auth.utils import get_or_create_user

logger = logging.getLogger(__name__)


class AuthService():
    """The AuthService provides an interface for querying the
    auth(n|z) framework within MyTardis. The auth service works by
    reading the class path to plugins from the settings file.

    :param settings: the settings object that contains the list of
       user and group plugins.
    :type settings: :py:class:`django.conf.settings`

    """

    def __init__(self, settings=settings):
        self._group_providers = []
        self._user_providers = []
        self._authentication_backends = {}
        self._initialised = False
        self.settings = settings

    def _manual_init(self):
        """Manual init had to be called by all the functions of the AuthService
        class to initialise the instance variables. This block of code used to
        be in the __init__ function but has been moved to its own init function
        to get around the problems with cyclic imports to static variables
        being exported from auth related modules.

        """
        for gp in self.settings.GROUP_PROVIDERS:
            self._group_providers.append(self._safe_import(gp))
        for up in self.settings.USER_PROVIDERS:
            self._user_providers.append(self._safe_import(up))
        for authenticationBackend in self.settings.AUTH_PROVIDERS:
            self._authentication_backends[authenticationBackend[0]] = \
                self._safe_import(authenticationBackend[2])
        self._initialised = True

    def _safe_import(self, path):
        try:
            dot = path.rindex('.')
        except ValueError:
            raise ImproperlyConfigured('%s isn\'t a middleware module' % path)
        auth_module, auth_classname = path[:dot], path[dot + 1:]
        try:
            mod = import_module(auth_module)
        except ImportError as e:
            raise ImproperlyConfigured('Error importing auth module %s: "%s"' %
                                       (auth_module, e))
        try:
            auth_class = getattr(mod, auth_classname)
        except AttributeError:
            raise ImproperlyConfigured(
                'Auth module "%s" does not define a "%s" class' %
                (auth_module, auth_classname))

        auth_instance = auth_class()
        return auth_instance

    def _get_or_create_user_from_dict(self, user_dict, auth_method):
        (user, created) = get_or_create_user(auth_method, user_dict['id'])
        if user and created:
            self._set_user_from_dict(user, user_dict, auth_method)
        return user

    def _set_user_from_dict(self, user, user_dict, auth_method):
        for field in ['first_name', 'last_name', 'email']:
            if field not in user_dict:
                logger.warning('%s.get_user did not return %s' %
                               (auth_method, field))
        user.email = user_dict.get('email', '')
        user.first_name = user_dict.get('first_name', '')
        user.last_name = user_dict.get('last_name', '')

        user.save()
        user.user_permissions.add(Permission.objects.get(codename='add_experiment'))
        user.user_permissions.add(Permission.objects.get(codename='change_experiment'))
        user.user_permissions.add(Permission.objects.get(codename='change_group'))
        user.user_permissions.add(Permission.objects.get(codename='change_userauthentication'))
        user.user_permissions.add(Permission.objects.get(codename='change_experimentacl'))
        user.user_permissions.add(Permission.objects.get(codename='change_datasetacl'))
        user.user_permissions.add(Permission.objects.get(codename='change_datafileacl'))

        user.user_permissions.add(Permission.objects.get(codename='add_datafile'))
        user.user_permissions.add(Permission.objects.get(codename='change_dataset'))

    def get_or_create_user(self, user_obj_or_dict, authMethod=None):
        '''
        refactored out for external use by AAF and possibly others
        '''
        if not self._initialised:
            self._manual_init()
        if authMethod is None:
            # pick default Django auth
            authMethod = getattr(settings, 'DEFAULT_AUTH', 'localdb')
        if isinstance(user_obj_or_dict, dict):
            user_dict = user_obj_or_dict
            user_obj_or_dict = self._get_or_create_user_from_dict(
                user_dict, authMethod)
        if isinstance(user_obj_or_dict, User):
            return user_obj_or_dict
        return None

    def authenticate(self, authMethod, **credentials):
        """Try and authenticate the user using the auth type he/she
        specified to use and if authentication didn't work using that

        :param authMethod: the shortname of the auth method.
        :type authMethod: string
        :param credentials: the credentials as expected by the auth plugin
        :type credentials: kwargs
        :returns: authenticated User or None
        :rtype: User or None
        """
        if not self._initialised:
            self._manual_init()

        if authMethod is None or authMethod == "None":
            auth_methods = self._authentication_backends.keys()
        else:
            auth_methods = [authMethod]
        for auth_method in auth_methods:
            # authenticate() returns either a User or a dictionary describing a
            # user (id, email, first_name, last_name).
            authenticate_retval = self._authentication_backends[
                auth_method].authenticate(**credentials)
            user = self.get_or_create_user(authenticate_retval,
                                           auth_method)
            if user is not None:
                if getattr(settings, "ENABLE_EVENTLOG", False):
                    from tardis.apps.eventlog.utils import log
                    log(
                        action="USER_LOGIN_SUCCESS",
                        user=user,
                        extra={
                            "auth_method": auth_method
                        }
                    )
                return user

        if getattr(settings, "ENABLE_EVENTLOG", False):
            from tardis.apps.eventlog.utils import log
            log(
                action="USER_LOGIN_FAILURE",
                request=credentials.get("request")
            )

        return None

    def getUser(self, authMethod, user_id, force_user_create=False):
        """Return a user model based on the given auth method and user id.

        This function is responsible for creating the
        user within the Django DB and returning the resulting
        user model.
        """
        if not self._initialised:
            self._manual_init()

        user = None

        if authMethod in self._authentication_backends:
            try:
                # get_user returns either a User or a dictionary describing a
                # user (id, email, first_name, last_name).
                user = self._authentication_backends[authMethod].get_user(user_id)
            except (NotImplementedError, AttributeError):
                # For backwards compatibility
                try:
                    from ..models.access_control import UserAuthentication
                    # Check if the given username in combination with the
                    # auth method is already in the UserAuthentication table
                    user = UserAuthentication.objects.get(username=user_id,
                        authenticationMethod=authMethod).userProfile.user
                except UserAuthentication.DoesNotExist:
                    # As a last resort, create the user anyway. Not recommended
                    # as this could fill the db with non-existent users.
                    if force_user_create:
                        user = { 'id': user_id }

            if isinstance(user, dict):
                user_dict = user
                user = self._get_or_create_user_from_dict(user_dict, authMethod)

        if user is None:
            return None

        return user


    def getUsernameByEmail(self, authMethod, email):
        """Return a username given the auth method and email address of a user.
        """
        if not self._initialised:
            self._manual_init()

        username = None

        # If the auth method is set, use it, otherwise use the built-in
        # Django auth.
        if not authMethod or authMethod == localdb_auth_key:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(email=email)
                if user:
                    username = user.username
            except User.DoesNotExist:
                pass
        elif authMethod in self._authentication_backends:
            try:
                username = self._authentication_backends[authMethod].getUsernameByEmail(email)
            except (NotImplementedError, AttributeError):
                pass
        return username

    def getGroups(self, user):
        """
        :param User user: User
        :returns: a list of tuples containing pluginname and group id
        :rtype: list
        """
        if not self._initialised:
            self._manual_init()
        grouplist = []
        for gp in self._group_providers:
            # logger.debug("group provider: " + gp.name)
            for group in gp.getGroups(user):
                grouplist.append((gp.name, group))
        return grouplist

    def searchEntities(self, filter):
        """Return a list of users and/or groups

        """
        if not self._initialised:
            self._manual_init()

    def searchUsers(self, filter):
        """Return a list of users and/or groups

        """
        if not self._initialised:
            self._manual_init()

    def searchGroups(self, **kw):
        """
        basestring id: the value of the id to search for
        basestring name: the value of the displayname to search for
        int max_results: the maximum number of elements to return
        basestring sort_by: the attribute the users should be sorted on
        basestring plugin: restrict the search to the specific group \
            provider

        returns: a list of users and/or groups
        rtype: list
        """
        if not self._initialised:
            self._manual_init()
        result = []
        max_results = kw.get('max_results', '')
        sort_by = kw.get('sort_by', '')
        plugin = kw.get('plugin', '')

        # We apply sorting and slicing here across all sets, so don't
        # make the plugin do it
        if sort_by:
            del kw['sort_by']
        if max_results:
            del kw['max_results']
        if plugin:
            del kw['plugin']

        for gp in self._group_providers:
            if plugin:
                if gp.name != plugin:
                    continue
            for group in gp.searchGroups(**kw):
                group["pluginname"] = gp.name
                result.append(group)

        if sort_by:

            def cmp(x, y):
                return (x > y) - (x < y)

            def compare(a, b):
                return cmp(
                    a.get(sort_by, '').lower(),
                    b.get(sort_by, '').lower())

            result.sort(key=cmp_to_key(compare))

        if max_results:
            try:
                max_results = int(max_results)
                result = result[:max_results]
            except ValueError:
                pass

        return result

    def getGroupsForEntity(self, entity):
        """Return a list of the groups an entity belongs to

        :param entity: the entity to earch for, user or group.
        :type entity: string
        :returns: groups
        :rtype: Group

        The groups will be reurned as a list similar to::

           [{'name': 'Group 456', 'id': '2'},
           {'name': 'Group 123', 'id': '1'}]

        """
        if not self._initialised:
            self._manual_init()
        for gp in self._group_providers:
            for group in gp.getGroupsForEntity(entity):
                group["pluginname"] = gp.name
                yield group
