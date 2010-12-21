'''
Created on 10/12/2010

@author: Ulrich Felzmann
@author: Gerson Gelang
'''

from django.contrib.auth.models import User, Group
from django.conf import settings

from tardis.tardis_portal.auth.interfaces import GroupProvider
from tardis.tardis_portal.models import *
from tardis.tardis_portal.logger import logger

from suds.client import Client

EPN_LIST = "_epn_list"

def get_expids(epns):
    """
    Return the corresponding experiment ids for a list of (str)EPNs
    """
    # for complex queries with OR statements
    from django.db.models import Q
    queries = [Q(string_value=value) for value in epns]
    query = queries.pop()
    for item in queries:
        query |= item

    expids = []
    # filter for soft parameter 'EPN' and
    # list of epns the user is supposed to see
    for epn in ExperimentParameter.objects.filter(name__name='EPN').filter(query):
        expids += [epn.parameterset.experiment.id]
    return expids


class VblGroupProvider(GroupProvider):
    name = u'vbl_groups'

    def getGroups(self, request):
        """
        return an iteration of the available groups.
        """
        if not request.session.__contains__(EPN_LIST):
            return []
        epnList = request.session[EPN_LIST]
        return epnList

    def getGroupById(self, id):
        """
        return the group associated with the id::

            {"id": 123,
            "display": "Group Name",}

        """
        raise NotImplemented()


class Backend():
    """
    Authenticate against the VBL SOAP Webservice. It is assumed that the
    request object contains the username and password to be provided to the
    VBLgetExpIDs function.

    Function: VBLgetExpIDs
       Retrieves a list of Experiment Ids from BOSS
       ArgumentsUser: VBL username Password: VBL password
       Result: comma separated string with Experiment Ids

    a new local user is created if it doesn't already exist

    if the authentication succeeds, the groups are updated

    """
    def authenticate(self, request):
        username = request.POST['username']
        password = request.POST['password']

        if not username or not password:
            return None

        # authenticate user and update group memberships
        if not settings.VBLSTORAGEGATEWAY:
            return None

        client = Client(settings.VBLSTORAGEGATEWAY)
        client.set_options(cache=None)
        result = str(client.service.VBLgetExpIDs(username, password))
        if result == "None" or result.startswith('Error'):
            return None
        try:
            # check if the given username in combination with the VBL
            # auth method is already in the UserAuthentication table
            user = UserAuthentication.objects.get(username=username,
                authenticationMethod=UserAuthentication.VBL_METHOD).userProfile.user

        except UserAuthentication.DoesNotExist:
            # else, create a new user with a random password
            name = username.partition('@')[0]
            name = 'vbl_%s' % name[0:26]
            user = User(username=name,
                        password=User.objects.make_random_password(),
                        email=username)
            user.is_staff = True
            user.save()

            userProfile = UserProfile(user=user)
            userProfile.save()

            userAuth = UserAuthentication(userProfile=userProfile,
                username=username, authenticationMethod=UserAuthentication.VBL_METHOD)
            userAuth.save()

        # result contains comma separated list of epns
        request.session[EPN_LIST] = result.split(',')
        return user

    def get_user(self, user_id):
        raise NotImplemented()
