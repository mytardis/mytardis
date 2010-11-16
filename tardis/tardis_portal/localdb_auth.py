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
    u, created = User.objects.get_or_create(email=email,
        defaults={'username': email.split('@')[0],
        'password': generateRandomPassword(constants.RANDOM_PASSWORD_LENGTH)})
    if created:
        logger.debug("new user account created")
    else:
        logger.debug("user found in DB")
    return u


def generateRandomPassword(length):
    """Generate a random password with the specified length."""

    import random
    import string
    password = ''.join([random.choice(string.letters + string.digits) \
        for i in range(length)])
    return password
