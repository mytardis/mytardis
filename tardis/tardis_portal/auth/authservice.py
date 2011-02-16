from django.conf import settings
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.contrib import auth


class AuthService():
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

        """

        if not self._initialised:
            self._manual_init()

        if authMethod:
            if authMethod in self._authentication_backends:
                # note that it's the backend's job to create a user entry
                # for a user in the DB if he has successfully logged in using
                # the auth method he has picked and he doesn't exist in the DB
                return self._authentication_backends[
                    authMethod].authenticate(**credentials)
            else:
                return None
        else:
            return auth.authenticate(**credentials)

    def getGroups(self, request):
        """Return a list of tuples containing pluginname and group id

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
        if not self._initialised:
            self._manual_init()
        pass
