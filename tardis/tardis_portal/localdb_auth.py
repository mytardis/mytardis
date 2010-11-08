'''
Local DB Authentication module.

@author: Gerson Galang
'''

from django.contrib.auth.models import User
from tardis.tardis_portal.logger import logger
from tardis.tardis_portal import constants

def authenticate_user(username, password):
    pass


def get_username_for_email(email):
    pass


def get_email_for_user(username):
    pass


def get_or_create_user(email):
    # try and find a user using the email provided
    try:
        u = User.objects.get(email=email)
    except User.DoesNotExist:
        username = email.split('@')[0]
        u = User.objects.create_user(username, email,
            generateRandomPassword(constants.RANDOM_PASSWORD_LENGTH))
    
    return u


def generateRandomPassword(length):
    """Generate a random password with the specified length."""

    import random
    import string
    password = ''.join([random.choice(string.letters + string.digits) \
        for i in range(length)])
    return password
