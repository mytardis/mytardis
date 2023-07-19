'''
Created on 15/03/2011

@author: gerson
'''

from django.conf import settings
from django.contrib.auth.models import Group, User

from ..models.access_control import UserAuthentication


def get_or_create_user(auth_method, user_id, email=''):
    try:
        # check if the given username in combination with the
        # auth method is already in the UserAuthentication table
        user = UserAuthentication.objects.get(
            username=user_id,
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


def configure_user(user):
    """ Configure a user account that has just been created by adding
    the user to the default groups and marking it as a not a Django
    account.

    :param User user: the User instance for the newly created account
    :returns: User profile for user
    :rtype: UserProfile
    """
    for group_name in settings.NEW_USER_INITIAL_GROUPS:
        try:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
        except Group.DoesNotExist:
            pass
    user.userprofile.isDjangoAccount = False
    user.userprofile.save()
    return user.userprofile
