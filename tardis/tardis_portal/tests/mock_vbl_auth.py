'''
Created on 24/01/2011

@author: gerson
'''
from tardis.tardis_portal.models import *
from django.contrib.auth.models import User, AnonymousUser
from tardis.tardis_portal.auth.vbl_auth import auth_key, EPN_LIST

auth_key = auth_key
EPN_LIST = EPN_LIST


class MockBackend():
    """
    Authenticate against the VBL SOAP Webservice. It is assumed that the
    request object contains the username and password to be provided to the
    VBLgetExpIDs function.

    a new local user is created if it doesn't already exist

    if the authentication succeeds, the session will contain a VBL
    session key used for downloads as well as the user's EPN list

    """

    def authenticate(self, request):
        username = request.POST['username']
        password = request.POST['password']

        if not username or not password:
            return None

        if username != 'test@test.com':
            return None
        elif password != 'testpass':
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
                password = User.objects.make_random_password()
                user = User.objects.create_user(name, password, username)
                user.save()

            try:
                # we'll also try and check if the user already has an
                # existing userProfile attached to his/her account
                userProfile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                userProfile = UserProfile(user=user, isDjangoAccount=True)
                userProfile.save()

            userAuth = UserAuthentication(userProfile=userProfile,
                username=username, authenticationMethod=auth_key)
            userAuth.save()

        # result contains comma separated list of epns
        request.session[EPN_LIST] = 'has been set'
        return user

    def get_user(self, user_id):
        raise NotImplemented()
