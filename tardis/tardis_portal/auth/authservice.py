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

from django.conf import settings
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.contrib import auth
from tardis.tardis_portal.staging import get_full_staging_path


class AuthService():
    """The AuthService provides an interface for querying the
    auth(n|z) framework within MyTARDIS. The auth service works by
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
        except ImportError, e:
            raise ImproperlyConfigured('Error importing auth module %s: "%s"' %
                                       (auth_module, e))
        try:
            auth_class = getattr(mod, auth_classname)
        except AttributeError:
            raise ImproperlyConfigured('Auth module "%s" does not define a "%s" class' %
                                       (auth_module, auth_classname))

        auth_instance = auth_class()
        return auth_instance

    def authenticate(self, authMethod, **credentials):
        """Try and authenticate the user using the auth type he/she
        specified to use and if authentication didn't work using that
        method, try each Django AuthProvider.

        :param authMethod: the shortname of the auth method.
        :type authMethod: string
        :param **credentials: the credentials as expected by the auth plugin
        :type **credentials: kwargs
        """

        if not self._initialised:
            self._manual_init()
        # if authMethod, else fall back to Django internal auth
        if authMethod:
            if authMethod in self._authentication_backends:
                # note that it's the backend's job to create a user entry
                # for a user in the DB if he has successfully logged in using
                # the auth method he has picked and he doesn't exist in the DB
                user = self._authentication_backends[
                    authMethod].authenticate(**credentials)
                if isinstance(user, dict):
                    user['pluginname'] = authMethod
                    return self.getUser(user)
                return user
            else:
                return None
        else:
            return auth.authenticate(**credentials)

    def getGroups(self, request):
        """Return a list of tuples containing pluginname and group id

        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`
        """
        if not self._initialised:
            self._manual_init()
        grouplist = []
        for gp in self._group_providers:
            # logger.debug("group provider: " + gp.name)
            for group in gp.getGroups(request):
                grouplist.append((gp.name, group))
        return grouplist

    def searchEntities(self, filter):
        """Return a list of users and/or groups

        """
        if not self._initialised:
            self._manual_init()
        pass

    def searchUsers(self, filter):
        """Return a list of users and/or groups

        """
        if not self._initialised:
            self._manual_init()
        pass

    def searchGroups(self, **kw):
        """Return a list of users and/or groups

        :param id: the value of the id to search for
        :param name: the value of the displayname to search for
        :param max_results: the maximum number of elements to return
        :param sort_by: the attribute the users should be sorted on
        :param plugin: restrict the search to the specific group provider
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
                if not gp.name == plugin:
                    continue
            for group in gp.searchGroups(**kw):
                group["pluginname"] = gp.name
                result.append(group)

        if sort_by:
            result.sort(lambda a, b: cmp(a.get(sort_by, '').lower(),
                                         b.get(sort_by, '').lower()))

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

    def getUser(self, user_dict):
        """Return a user model based on the user dict.

        This function is responsible for creating the
        user within the Django DB and returning the resulting
        user model.
        """
        from django.contrib.auth.models import User
        from tardis.tardis_portal.models import UserProfile, UserAuthentication

        if not self._initialised:
            self._manual_init()

        plugin = user_dict['pluginname']

        username = ''
        if not 'id' in user_dict:
            email = user_dict['email']
            username =\
                self._authentication_backends[plugin].getUsernameByEmail(email)
        else:
            username = user_dict['id']

        try:
            user = UserAuthentication.objects.get(username=username,
                            authenticationMethod=plugin).userProfile.user
            return user
        except UserAuthentication.DoesNotExist:
            pass

        # length of the maximum username
        max_length = 30

        # the username to be used on the User table
        if username.find('@') > 0:
            unique_username = username.partition('@')[0][:max_length]
        else:
            unique_username = username[:max_length]

        # Generate a unique username
        i = 0
        try:
            while (User.objects.get(username=unique_username)):
                i += 1
                unique_username = username[:max_length - len(str(i))] + str(i)
        except User.DoesNotExist:
            pass

        password = User.objects.make_random_password()
        user = User.objects.create_user(username=unique_username,
                                        password=password,
                                        email=user_dict.get("email", ""))
        user.save()

        userProfile = UserProfile(user=user,
                                  isDjangoAccount=False)
        userProfile.save()

        userAuth = UserAuthentication(userProfile=userProfile,
            username=username, authenticationMethod=plugin)
        userAuth.save()

        if settings.STAGING_PROTOCOL == plugin:
            # to be put in its own function
            staging_path = get_full_staging_path(username)
            import os
            if not os.path.exists(staging_path):
                os.makedirs(staging_path)
                os.system('chmod g+w ' + staging_path)
                os.system('chown ' + username + ' ' + staging_path)

        return user
