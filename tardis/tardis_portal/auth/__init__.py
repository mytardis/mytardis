from django.conf import settings
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.contrib import auth
from tardis.tardis_portal.auth.interfaces import AuthProvider, UserProvider, GroupProvider


class AuthService:
    def __init__(self, settings=settings):
        self._group_providers = []
        self._user_providers = []
        self._authentication_backends = {}

        for gp in settings.GROUP_PROVIDERS:
            self._group_providers.append(self._safe_import(gp))
        for up in settings.USER_PROVIDERS:
            self._user_providers.append(self._safe_import(up))
        for authenticationBackend in settings.AUTH_PROVIDERS:
            self._authentication_backends[authenticationBackend[0]] = \
                self._safe_import(authenticationBackend[2])

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
        """
        Try and authenticate the user using the auth type he/she specified to
        use and if authentication didn't work using that method, try each
        Django AuthProvider.
        """
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

        from django.conf import settings
        settings.AUTHENTICATION_BACKENDS = ()

        for up in self._user_providers:
            settings.AUTHENTICATION_BACKENDS += up

        try:
            user = authenticate(username=username, password=password)
        except User.DoesNotExist:
            return None


    def getGroups(self, request):
        """
        return a list of tuples containing pluginname and group id
        """
        for gp in self._group_providers:
            for group in gp.getGroups(request):
                yield (gp.name, group)

    def searchEntities(self, filter):
        """
        return a list of users and/or groups
        """
        pass

    def searchUsers(self, filter):
        """
        return a list of users and/or groups
        """
        pass

    def searchGroups(self, **kw):
        """
        return a list of users and/or groups
        :param id: the value of the id to search for
        :param name: the value of the displayname to search for
        :param max_results: the maximum number of elements to return
        :param sort_by: the attribute the users should be sorted on
        """

        result = []
        max_results = kw.get('max_results', '')
        sort_by = kw.get('sort_by', '')

        # We apply sorting and slicing here across all sets, so don't
        # make the plugin do it
        if sort_by:
            del kw['sort_by']
        if max_results:
            del kw['max_results']

        for gp in self._group_providers:
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
        """
        return a list of the groups an entity belongs to::

           [{'name': 'Group 456', 'id': '2'},
           {'name': 'Group 123', 'id': '1'}]

        """
        for gp in self._group_providers:
            for group in gp.getGroupsForEntity(entity):
                group["pluginname"] = gp.name
                yield group

    def getUser(self, user_dict):
        """
        return a user model based on the user dict.

        This function is responsible for creating the
        user within the Django DB and returning the resulting
        user model.
        """
        pass

auth_service = AuthService()


class LazyGroups(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_groups'):
            request._cached_groups = auth_service.getGroups(request)
        return request._cached_groups


class AuthorizationMiddleware(object):
    def process_request(self, request):
        assert hasattr(request, 'session'), "The Django authorization middleware requires session middleware to be installed. Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.sessions.middleware.SessionMiddleware'."
        request.__class__.groups = LazyGroups()
        return None
