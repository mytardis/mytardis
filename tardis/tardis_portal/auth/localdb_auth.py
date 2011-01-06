'''
Local DB Authentication module.

@author: Gerson Galang
'''

from django.contrib.auth.models import User, Group
from django.contrib.auth.backends import ModelBackend

from tardis.tardis_portal.auth.interfaces import GroupProvider, UserProvider
from tardis.tardis_portal.logger import logger
from tardis.tardis_portal import constants

auth_key = u'localdb'
auth_display_name = u'Local DB'

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


class DjangoAuthBackend():
    """Authenticate against Django's Model Backend.

    """
    def authenticate(self, request):
        username = request.POST['username']
        password = request.POST['password']
        if not username or not password:
            return None
        return _modelBackend.authenticate(username, password)

    def get_user(self, user_id):
        return _modelBackend.get_user(user_id)



_modelBackend = ModelBackend()



class DjangoGroupProvider(GroupProvider):
    name = u'django_groups'

    def getGroups(self, request):
        """
        return an iteration of the available groups.
        """
        return request.user.groups.all()

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
    name = u'django_users'

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
