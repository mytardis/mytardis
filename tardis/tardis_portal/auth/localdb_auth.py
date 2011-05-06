'''
Local DB Authentication module.

.. moduleauthor:: Gerson Galang <gerson.galang@versi.edu.au>
'''

import logging

from django.contrib.auth.models import User, Group
from django.contrib.auth.backends import ModelBackend

from tardis.tardis_portal.auth.interfaces import GroupProvider, UserProvider


logger = logging.getLogger(__name__)


auth_key = u'localdb'
auth_display_name = u'Local DB'


# TODO: remove these functions, they should be obsolete! [UF]
def get_username_for_email(email):
    raise NotImplemented()


def get_email_for_user(username):
    raise NotImplemented()


def get_or_create_user(email):
    u, created = User.objects.get_or_create(email=email,
        defaults={'username': email.split('@')[0],
        'password': User.objects.make_random_password()})
    if created:
        logger.debug("new user account created")
    else:
        logger.debug("user found in DB")
    return u


_modelBackend = ModelBackend()


class DjangoAuthBackend():
    """Authenticate against Django's Model Backend.

    """

    def authenticate(self, request):
        """authenticate a user, this expect the user will be using
        form based auth and the *username* and *password* will be
        passed in as **POST** variables.

        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`
        """
        username = request.POST['username']
        password = request.POST['password']

        if not username or not password:
            return None
        return _modelBackend.authenticate(username, password)

    def get_user(self, user_id):
        return _modelBackend.get_user(user_id)


class DjangoGroupProvider(GroupProvider):
    name = u'django_group'

    def getGroups(self, request):
        """return an iteration of the available groups.
        """
        groups = request.user.groups.all()
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
            "display": "John Smith",
            "email": "john@example.com"}

        """
        userObj = User.objects.get(id=id)
        if userObj:
            return {'id': id, 'display': userObj.first_name + ' ' +
                userObj.last_name, 'email': userObj.email}
        return None


django_user = DjangoUserProvider.name
django_group = DjangoGroupProvider.name
