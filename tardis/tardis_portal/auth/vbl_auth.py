'''
Created on 10/12/2010

@author: Ulrich Felzmann
'''

from django.contrib.auth.models import User, Group
from django.conf import settings

from tardis.tardis_portal.models import *
from tardis.tardis_portal.logger import logger

from suds.client import Client

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


class Backend():
    """
    Authenticate against the VBL SOAP Webservice

    Function: VBLgetExpIDs
       Retrieves a list of Experiment Ids from BOSS
       ArgumentsUser: VBL username Password: VBL password
       Result: comma separated string with Experiment Ids

    a new local user is created if it doesn't already exist

    if the authentication succeeds, the groups are updated

    """
    def authenticate(self, username=None, password=None):
        # authenticate user and update group memberships
        if not settings.VBLSTORAGEGATEWAY:
            return None

        client = Client(settings.VBLSTORAGEGATEWAY)
        client.set_options(cache=None)
        result = str(client.service.VBLgetExpIDs(username, password))
        if result == None or result.startswith('Error'):
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
    
        return user

    def get_user(self, user_id):
        raise NotImplemented()
