class AuthProvider:
    def authenticate(self, request):
        """
        from a request authenticate try to authenticate the user.
        return a user dict if successful.
        """
        raise NotImplemented()


class UserProvider:
    def getUserById(self, id):
        """
        return the user dictionary in the format of::

            {"id": 123,
            "display": "John Smith",
            "email": "john@example.com"}

        """
        raise NotImplemented()

    def searchUsers(self, request):
        """
        return a list of user descriptions from the auth domain.

        each user is in the format of::

            {"id": 123,
            "display": "John Smith",
            "email": "john@example.com"}

        """
        raise NotImplemented()


class GroupProvider:
    def getGroups(self, request):
        """
        return an iteration of the available groups.
        """
        raise NotImplemented()

    def getGroupById(self, id):
        """
        return the group associated with the id
        """
        raise NotImplemented()

    def searchGroups(self, filter):
        """
        return a list of groups that match the filter
        """
        raise NotImplemented()

    def getGroupsForEntity(self, id):
        """
        return a list of groups associated with a particular entity id
        """
        raise NotImplemented()
