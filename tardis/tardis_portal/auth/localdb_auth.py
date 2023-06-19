'''
Local DB Authentication module.

.. moduleauthor:: Gerson Galang <gerson.galang@versi.edu.au>
'''

import logging

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Group, User

from .interfaces import AuthProvider, GroupProvider, UserProvider

logger = logging.getLogger(__name__)


auth_key = u'localdb'
auth_display_name = u'Local DB'


_modelBackend = ModelBackend()


class DjangoAuthBackend(AuthProvider):
    """Authenticate against Django's Model Backend.

    """

    def authenticate(self, request):
        """authenticate a user, this expect the user will be using
        form based auth and the *username* and *password* will be
        passed in as **POST** variables.

        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`
        :returns: authenticated User
        :rtype: User
        """
        username = request.POST['username']
        password = request.POST['password']

        if not username or not password:
            return None
        return _modelBackend.authenticate(request, username, password)

    def get_user(self, user_id):
        try:
            user = User.objects.get(username=user_id)
        except User.DoesNotExist:
            user = None
        return user


class DjangoGroupProvider(GroupProvider):
    name = u'django_group'

    def getGroups(self, user):
        """return an iteration of the available groups.
        """
        groups = user.groups.all()
        return [g.id for g in groups]

    def getGroupById(self, id):
        """return the group associated with the id::

            {"id": 123,
            "display": "Group Name",}

        """
        groupObj = Group.objects.get(id=id)
        if groupObj:
            return {'id': id, 'display': groupObj.name}
        return None

    def searchGroups(self, **filter):
        result = []
        groups = Group.objects.filter(**filter)
        for g in groups:
            users = [u.username for u in User.objects.filter(groups=g)]
            result += [{'id': g.id,
                        'display': g.name,
                        'members': users}]
        return result


class DjangoUserProvider(UserProvider):
    name = u'django_user'

    def getUserById(self, id):
        """
        return the user dictionary in the format of::

            {"id": 123,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com"}

        """
        try:
            userObj = User.objects.get(username=id)
            return {'id': id,
                    'first_name': userObj.first_name,
                    'last_name': userObj.last_name,
                    'email': userObj.email}
        except User.DoesNotExist:
            return None


django_user = DjangoUserProvider.name
django_group = DjangoGroupProvider.name
