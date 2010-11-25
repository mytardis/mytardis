'''
Created on 25/11/2010

@author: gerson
'''

from tardis.tardis_portal.auth.interfaces import GroupProvider, UserProvider
from django.contrib.auth.models import User, Group

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
            return {'id': id, 'display': userObj.first_name + ' ' + \
                    userObj.last_name, 'email': userObj.email}
        return None
