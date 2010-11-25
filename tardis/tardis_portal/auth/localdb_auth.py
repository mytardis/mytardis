'''
Local DB Authentication module.

@author: Gerson Galang
'''

from django.contrib.auth.models import User, Group
from tardis.tardis_portal.auth.interfaces import GroupProvider, UserProvider
from tardis.tardis_portal.logger import logger
from tardis.tardis_portal import constants

def authenticate_user(username, password):
    pass


def get_username_for_email(email):
    pass


def get_email_for_user(username):
    pass


def get_or_create_user(email):
    u, created = User.objects.get_or_create(email=email,
        defaults={'username': email.split('@')[0],
        'password': generateRandomPassword(constants.RANDOM_PASSWORD_LENGTH)})
    if created:
        logger.debug("new user account created")
    else:
        logger.debug("user found in DB")
    return u


def generateRandomPassword(length):
    """Generate a random password with the specified length."""

    import random
    import string
    password = ''.join([random.choice(string.letters + string.digits) \
        for i in range(length)])
    return password


class DjangoGroupProvider(GroupProvider):
    
    def getGroups(self, request):
        """
        return an iteration of the available groups.
        """
        return request.user.groups

    def getGroupById(self, id):
        """
        return the group associated with the id::

            {"id": 123,
            "display": "Group Name",}
            
        """
        groupObj = Group.objects.get(id=id)
        if groupObj:
            return {'id': id, 'display': groupObj.name}
        return None


class DjangoUserProvider(UserProvider):

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
