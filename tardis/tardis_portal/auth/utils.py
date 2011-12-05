'''
Created on 15/03/2011

@author: gerson
'''

from django.contrib.auth.models import User
from tardis.tardis_portal.models import UserProfile, UserAuthentication


def get_or_create_user(auth_method, user_id, email=''):
    try:
        # check if the given username in combination with the
        # auth method is already in the UserAuthentication table
        user = UserAuthentication.objects.get(username=user_id,
            authenticationMethod=auth_method).userProfile.user
        created = False
    except UserAuthentication.DoesNotExist:
        user = create_user(auth_method, user_id, email)
        created = True
    return (user, created)


def create_user(auth_method, user_id, email=''):
    # length of the maximum username
    max_length = 30

    # the username to be used on the User table
    if user_id.find('@') > 0:
        unique_username = user_id.partition('@')[0][:max_length]
    else:
        unique_username = user_id[:max_length]

    # Generate a unique username
    i = 0
    try:
        while (User.objects.get(username=unique_username)):
            i += 1
            unique_username = user_id[:max_length - len(str(i))] + str(i)
    except User.DoesNotExist:
        pass

    password = User.objects.make_random_password()
    user = User.objects.create_user(username=unique_username,
                                    password=password,
                                    email=email)
    user.save()

    userProfile = UserProfile(user=user, isDjangoAccount=False)
    userProfile.save()

    userAuth = UserAuthentication(userProfile=userProfile,
        username=user_id, authenticationMethod=auth_method)
    userAuth.save()

    return user

