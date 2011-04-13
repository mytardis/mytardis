'''
Created on 15/03/2011

@author: gerson
'''


from django.contrib.auth.models import User, AnonymousUser
from tardis.tardis_portal.models import UserProfile, UserAuthentication


def get_or_create_user_with_username(request, username, auth_key):
    isDjangoAccount = True

    try:
        # check if the given username in combination with the LDAP
        # auth method is already in the UserAuthentication table
        user = UserAuthentication.objects.get(username=username,
            authenticationMethod=auth_key).userProfile.user

    except UserAuthentication.DoesNotExist:
        # if request.user is not null, then we can assume that we are only
        # calling this function to verify if the provided username and
        # password will authenticate with the provided backend
        if type(request.user) is not AnonymousUser:
            user = request.user

        # else, create a new user with a random password
        else:
            isDjangoAccount = False

            if username.find('@') > 0:
                # the username to be used on the User table
                name = username.partition('@')[0]
            else:
                name = username

            # length of the maximum username and the separator `_`
            max_length = 31 - len(name)
            name = '%s_%s' % (auth_key, name[0:max_length])
            password = User.objects.make_random_password()
            user = User.objects.create_user(username=name,
                                            password=password,
                                            email=username)
            user.save()

        try:
            # we'll also try and check if the user already has an
            # existing userProfile attached to his/her account
            userProfile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            userProfile = UserProfile(user=user,
                isDjangoAccount=isDjangoAccount)
            userProfile.save()

        userAuth = UserAuthentication(userProfile=userProfile,
            username=username, authenticationMethod=auth_key)
        userAuth.save()

    return user
