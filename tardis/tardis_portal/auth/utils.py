'''
Created on 15/03/2011

@author: gerson
'''

from django.conf import settings
from django.contrib.auth.models import User, Group
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
    max_length = 254

    # the username to be used on the User table
    # if user_id.find('@') > 0:
    #     username_prefix = user_id.partition('@')[0][:max_length]
    # else:
    #     username_prefix = user_id[:max_length]
    unique_username = user_id[:max_length]
    username_prefix = unique_username
    # Generate a unique username
    i = 0
    try:
        while (User.objects.get(username=unique_username)):
            i += 1
            unique_username = username_prefix[
                :max_length - len(str(i))] + str(i)
    except User.DoesNotExist:
        pass

    password = User.objects.make_random_password()
    user = User.objects.create_user(username=unique_username,
                                    password=password,
                                    email=email)
    user.save()
    userProfile = configure_user(user)
    userAuth = UserAuthentication(
        userProfile=userProfile,
        username=user_id, authenticationMethod=auth_method)
    userAuth.save()

    return user


def configure_user(user, isDjangoAccount=False):
    """ Configure a user account that has just been created by adding
    the user to the default groups and creating a UserProfile if
    necessary.

    This method can be called multiple times - each subsequent call
    will only update isDjangoAccount and return the previously created
    UserProfile.

    Creating a User record (either from Django Admin or from within
    MyTardis's code) will send a post_save signal defined in
    tardis.tardis_portal.filters.FilterInitMiddleware which will call this
    method to add the user to the default groups and to create a default
    UserProfile with isDjangoAccount=True.

    For external accounts (e.g. LDAP), this method can be called a second
    time to set isDjangoAccount to False, and to retrieve the UserProfile
    in order to create a UserAuthentication record.

    :param user: the User instance for the newly created account
    """
    for group_name in settings.NEW_USER_INITIAL_GROUPS:
        try:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
        except Group.DoesNotExist:
            pass
    try:
        userProfile = UserProfile.objects.get(user=user)
        userProfile.isDjangoAccount = isDjangoAccount
    except UserProfile.DoesNotExist:
        userProfile = UserProfile(user=user, isDjangoAccount=isDjangoAccount)
    userProfile.save()
    return userProfile
