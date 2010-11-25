from tardis.tardis_portal.auth.interfaces import AuthProvider, UserProvider, GroupProvider


class AuthService:
    def authenticate(self, request):
        """
        Try and authenticate the user first using Django auth backends,
        then try each AuthProvider.
        """
        pass

    def getGroups(self, request):
        """
        return a list of tuples containing pluginname and group id
        """
        pass

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

    def searchGroups(self, filter):
        """
        return a list of users and/or groups
        """
        pass

    def getGroupsForEntity(self, entity):
        """
        Look in UserAuthentation, pull auth sources and query approprate
        auth plugins.
        """
        pass

    def getUser(self, user_dict):
        """
        return a user model based on the user dict.

        This function is responsible for creating the
        user within the Django DB and returning the resulting
        user model.
        """
        pass

