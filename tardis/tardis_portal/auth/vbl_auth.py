'''
Created on 10/12/2010

@author: Ulrich Felzmann
@author: Gerson Galang
'''

from django.contrib.auth.models import User, Group, AnonymousUser
from django.conf import settings

from tardis.tardis_portal.auth.interfaces import GroupProvider
from tardis.tardis_portal.models import *
from tardis.tardis_portal.logger import logger

from suds.client import Client


EPN_LIST = "_epn_list"

auth_key = u'vbl'
auth_display_name = u'VBL'

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
            # check if the user is linked to any experiments
            if not settings.VBLSTORAGEGATEWAY:
                return []

            client = Client(settings.VBLSTORAGEGATEWAY)
            client.set_options(cache=None)

            try:
                # check if a user exists that can authenticate using the VBL
                # auth method
                userAuth = UserAuthentication.objects.get(
                    userProfile__user=request.user,
                    authenticationMethod=auth_key)

            except UserAuthentication.DoesNotExist:
                return []

            result = str(
                client.service.VBLgetExpIDsFromEmail(userAuth.username))
            return result.split(',')
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
                authenticationMethod=auth_key).userProfile.user

        except UserAuthentication.DoesNotExist:
            # if request.user is not null, then we can assume that we are only
            # calling this function to verify if the provided username and
            # password will authenticate with this backend
            if type(request.user) is not AnonymousUser:
                user = request.user
                
            # else, create a new user with a random password
            else:
                name = username.partition('@')[0]
                name = 'vbl_%s' % name[0:26]
                user = User(username=name,
                            password=User.objects.make_random_password(),
                            email=username)
                user.is_staff = True
                user.save()

            try:
                # we'll also try and check if the user already has an
                # existing userProfile attached to his/her account
                userProfile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                userProfile = UserProfile(user=user, isNotADjangoAccount=True)
                userProfile.save()

            userAuth = UserAuthentication(userProfile=userProfile,
                username=username, authenticationMethod=auth_key)
            userAuth.save()

        # result contains comma separated list of epns
        request.session[EPN_LIST] = result.split(',')
        return user

    def get_user(self, user_id):
        raise NotImplemented()
