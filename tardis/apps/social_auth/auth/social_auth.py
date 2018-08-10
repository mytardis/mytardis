import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.core.mail import get_connection
from django.contrib.auth.models import Permission

from celery.task import task

from tardis.tardis_portal.models import UserAuthentication

logger = logging.getLogger(__name__)


def add_authentication_method(**kwargs):
    """Creates an authentication record for OpenID authenticated user"""
    # add authentication method only if is a new user
    isNewUser = kwargs.get('is_new')
    if not isNewUser:
        return None

    backend = kwargs.get('backend')
    authenticatedBackendName = type(backend).__name__
    user = kwargs.get('user')
    # get auth method from backend
    authMethod = get_auth_method(authenticatedBackendName)

    try:
        authentication = UserAuthentication(userProfile=user.userprofile,
                                            username=user.username,
                                            authenticationMethod=authMethod,
                                            approved=False)
        authentication.save()
        kwargs['authentication'] = authentication
    except:
        pass
    return kwargs


def get_auth_method(authenticatedBackendName):
    """
    Return matching user authentication method from list of authentication
    methods in settings
    """

    for authKey, authDisplayName, authBackend in settings.AUTH_PROVIDERS:
        authBackendClassName = authBackend.split('.')[-1]
        if authBackendClassName == authenticatedBackendName:
            return authKey
    return None


def add_user_permissions(**kwargs):
    """
    Adds default permission to OpenID authenticated user
    """
    user = kwargs.get('user')
    if user:
        for perm in ['add_experiment', 'change_experiment', 'change_group',
                     'change_userauthentication', 'change_objectacl',
                     'add_datafile', 'change_dataset']:
            user.user_permissions.add(Permission.objects.get(codename=perm))

    return kwargs


def approve_user_auth(**kwargs):
    """
    Sets approved status to True in user authentication
    This will add user permissions as well.
    """
    '''
    :param kwargs:
    :return: kwargs
    '''

    isNewUser = kwargs.get('is_new')
    if not isNewUser:
        return None

    authentication = kwargs.get('authentication')
    authentication.approved = True
    authentication.save()
    return kwargs


def send_admin_email(**kwargs):
    """
    Sends MyTardis admins an email for approving account
    """

    isNewUser = kwargs.get('is_new')
    if not isNewUser:
        return None

    # get user
    user = kwargs.get('user')
    if user:
        authentication = kwargs.get('authentication')
        # send email to admins
        site = Site.objects.get_current().domain
        subject = '[MyTardis] User account needs admin approval'
        message = (
            "Hi, This message is for MyTardis Admins.\n\n"
            "A MyTardis user account with username as \"%s\" and user_id as "
            "\"%s\" was recently created and needs admin approval.\n\n"
            "%s/admin/tardis_portal/userauthentication/%s\n\n"
            "Thanks,\n"
            "MyTardis\n"
            % (user.username, user.id, site, authentication.id))

        try:
            mail.mail_admins(subject, message,
                             connection=get_connection(fail_silently=True))

        except Exception as e:
            logger.error("There was an error sending mail: %s ", e)

    return kwargs


@task(name="social_auth_account_approved", ignore_result=True)
def send_account_approved_email(user):
    """Sends user email once account is approved by admin"""
    site_title = getattr(settings, 'SITE_TITLE', 'MyTardis')
    subject = '[MyTardis] User account Approved'
    message = (
        "Hi %s , \n\nWelcome to %s. "
        "Your account has been approved. "
        "Please use  the \"Sign in with Google\" button on the login page to "
        "log in to %s. "
        "If you have an existing %s would like to "
        "migrate your data and settings to your new account, "
        "follow the instructions on\n\n"
        "Thanks,\n"
        "MyTardis\n"
        % (user.username, site_title, site_title, site_title))
    try:
        from_email = getattr(settings, 'OPENID_FROM_EMAIL', None)
        user.email_user(
            subject, message, from_email=from_email, fail_silently=True)

    except Exception as e:
        logger.error("There was an error sending mail: %s ", e)
