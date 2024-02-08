"""
Created on 15/03/2011

@author: gerson

Updated on 14/12/2023

@author: Chris Seal
"""


import contextlib
import secrets
from typing import Optional, Tuple

from django.conf import settings
from django.contrib.auth.models import Group, User

from ..models.access_control import UserAuthentication

alphabet: str = (
    r"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!$%^&*();:[]{}"
)


def gen_random_password(
    length: Optional[int],
    allowed_chars: Optional[str],
) -> str:
    """Replacement function for deprecated User.make_random_password"""
    if not length:
        length = 10
    if not allowed_chars:
        allowed_chars = alphabet
    return "".join(secrets.choice(allowed_chars) for _ in range(length))


def get_or_create_user(
    auth_method: str,
    user_id: str,
    email: str = "",
    password_length: Optional[int] = None,
    password_chars: Optional[str] = None,
) -> Tuple[User, bool]:
    try:
        # check if the given username in combination with the
        # auth method is already in the UserAuthentication table
        user = UserAuthentication.objects.get(
            username=user_id, authenticationMethod=auth_method
        ).userProfile.user
        created = False
    except UserAuthentication.DoesNotExist:
        user = create_user(
            auth_method,
            user_id,
            email=email,
            password_length=password_length,
            password_chars=password_chars,
        )
        created = True
    return (user, created)


def create_user(
    auth_method,
    user_id,
    email="",
    password_length: Optional[int] = None,
    password_chars: Optional[str] = None,
):
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
    with contextlib.suppress(User.DoesNotExist):
        while User.objects.get(username=unique_username):
            i += 1
            unique_username = username_prefix[: max_length - len(str(i))] + str(i)
    password = gen_random_password(password_length, password_chars)
    user = User.objects.create_user(
        username=unique_username, password=password, email=email
    )
    user.save()
    userProfile = configure_user(user)
    userAuth = UserAuthentication(
        userProfile=userProfile, username=user_id, authenticationMethod=auth_method
    )
    userAuth.save()

    return user


def configure_user(user):
    """Configure a user account that has just been created by adding
    the user to the default groups and marking it as a not a Django
    account.

    :param User user: the User instance for the newly created account
    :returns: User profile for user
    :rtype: UserProfile
    """
    for group_name in settings.NEW_USER_INITIAL_GROUPS:
        with contextlib.suppress(Group.DoesNotExist):
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
    user.userprofile.isDjangoAccount = False
    user.userprofile.save()
    return user.userprofile
