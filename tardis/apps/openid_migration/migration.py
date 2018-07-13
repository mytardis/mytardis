import logging

from django.http import HttpResponse
from django.contrib.auth.models import Permission
from django.core.mail import send_mail
from django.conf import settings

from tardis.tardis_portal.models import UserProfile, UserAuthentication, \
    ObjectACL, Group
from tardis.tardis_portal.auth.authentication import _getSupportedAuthMethods, \
    _getJsonFailedResponse, _setupJsonData, _getJsonSuccessResponse, _getJsonConfirmResponse
from tardis.tardis_portal.forms import createLinkedUserAuthenticationForm
from tardis.tardis_portal.auth import localdb_auth
from tardis.tardis_portal.shortcuts import render_response_index
from tardis.apps.openid_migration.models import OpenidUserMigration, OpenidACLMigration

from tastypie.models import ApiKey

from .email_text import email_migration_success
from . import default_settings
from .forms import openid_user_migration_form


logger = logging.getLogger(__name__)


def do_migration(request):
    """Migrating account from the account that the
    logged in  user has provided in the Authentication Form. Migration involve relinking
    the UserAuthentication table entries, transferring ObjectACL entries
    to the migrated account, changing the Group memberships and making
    the old account inactive.

    :param Request request: the HTTP request object

    :returns: The HttpResponse which contains request.user's new list of
        authentication methods
    :rtype: HttpResponse
    """

    from tardis.tardis_portal.auth import auth_service

    userAuthMethodList = []

    # the list of supported non-local DB authentication methods
    supportedAuthMethods = _getSupportedAuthMethods()

    authenticationMethod = 'localdb'
    # let's try and authenticate here
    user = auth_service.authenticate(authMethod="None",
        request=request)

    if user is None:
        errorMessage = 'Wrong username or password. Please try again'
        return _getJsonFailedResponse(errorMessage)

    # if has already registered to use the provided auth method, then we can't
    # link the auth method to the user
    if user != request.user:
        # TODO: find all the experiments "user" has access to and link
        # "request.user" to them
        logger.info("starting migration from %s to %s", user.username,
                    request.user.username)
        # check if the "request.user" has a userProfile
        userProfile, created = UserProfile.objects.get_or_create(
            user=request.user)

        logger.info("linking user authentication")
        # if he has, link 'user's UserAuthentication to it
        userAuths = UserAuthentication.objects.filter(
            userProfile__user=user)

        for userAuth in userAuths:
            # also remove the current userAuth from the list of authentication
            # method options that can be added by this user
            del supportedAuthMethods[userAuth.authenticationMethod]

        # let's search for the ACLs that refer to 'user' and transfer them
        # to request.user
        userIdToBeReplaced = user.id
        replacementUserId = request.user.id
        # for logging migration event
        user_migration_record = OpenidUserMigration(old_user=user, new_user=request.user,
                                                    old_user_auth_method=authenticationMethod,
                                                    new_user_auth_method='')
        user_migration_record.save()
        # TODO: note that django_user here has been hardcoded. Uli's going
        # to change the implementation on his end so that I can just use a key
        # in here instead of a hardcoded string.
        logger.info("Staring object ACL migration")
        acl_migration(userIdToBeReplaced, replacementUserId,
                      user_migration_record)
        # let's also change the group memberships of all the groups that 'user'
        # is a member of
        logger.info("Migrating user groups")
        groups = Group.objects.filter(user=user)
        logger.info("Number of groups found : %s", groups.count())
        for group in groups:
            request.user.groups.add(group)
        # change old user username to username_authmethod amd make it inactive
        old_username = user.username
        user.username = old_username + '_' + authenticationMethod
        logger.info("setting old use to inactive")
        user.is_active = False
        user.save()

        # change new user username to old user
        new_user = request.user
        new_user.username = old_username
        logger.info("changing new username %s to old username %s",
                    request.user.username, old_username)
        new_user.save()

        # copy api key from old user to new user so that MyData works seamlessly post migration
        logger.info("migrating api key")
        migrate_api_key(user, request.user)

        # migrate user permissions
        logger.info("migrating user permissions")
        migrate_user_permissions(user, request.user)

        # Add migration event record
        user_migration_record.migration_status = True
        user_migration_record.save()
        # send email for successful migration
        # TODO : get request user auth method
        logger.info("sending email to %s", user.email)
        notify_user(user, old_username, 'AAF')

    # data = _setupJsonData(authForm, authenticationMethod, supportedAuthMethods)
    return _getJsonSuccessResponse(data={})


def acl_migration(userIdToBeReplaced, replacementUserId, user_migration_record):
    experimentACLs = ObjectACL.objects.filter(
        pluginId='django_user',
        entityId=userIdToBeReplaced)

    logger.info("Found %s number of ACLs to migrate", experimentACLs.count())

    for experimentACL in experimentACLs:

        # now let's check if there's already an existing entry in the ACL
        # for the given experiment and replacementUserId
        try:
            acl = ObjectACL.objects.get(
                pluginId='django_user',
                entityId=replacementUserId,
                content_type=experimentACL.content_type,
                object_id=experimentACL.object_id
            )
            logger.info("found existing entry in the ACL "
                        "for the given experiment and replacementUserId")
            acl.canRead = acl.canRead or experimentACL.canRead
            acl.canWrite = acl.canWrite or experimentACL.canWrite
            acl.canDelete = acl.canDelete or acl.canDelete
            acl.save()
            experimentACL.delete()
        except ObjectACL.DoesNotExist:
            experimentACL.entityId = replacementUserId
            experimentACL.save()
            # record acl migration event
            logger.info("acl migrated %s", experimentACL.object_id)
            acl_migration_record = OpenidACLMigration(user_migration=user_migration_record,
                                                      acl_id=experimentACL)
            acl_migration_record.save()


def notify_user(user, old_username, new_authmethod):
    subject, message_content = email_migration_success(old_username, new_authmethod)
    try:
        user.email_user(subject,
                        message_content,
                        from_email=getattr(settings, 'OPENID_NOTIFICATION_SENDER_EMAIL',
                                           default_settings.OPENID_NOTIFICATION_SENDER_EMAIL),
                        fail_silently=True)
        logger.info("email sent")
    except Exception as e:
        logger.error(
            "failed to send migration notification email(s): %s" %
            repr(e)
        )


def migrate_user_permissions(old_user, new_user):
    # get old user permissions
    old_user_perms = Permission.objects.filter(user=old_user)
    logger.info("found %s number of permissions in old user record",
                old_user_perms.count())

    for perms in old_user_perms:
        # find if permission already exist
        try:
            new_user.user_permissions.get(codename=perms.codename)
        # add old user permissions to new user
        except Permission.DoesNotExist:
            new_user.user_permissions.add(perms)
            new_user.save()


def migrate_api_key(old_user, new_user):
    old_user_api_key = get_api_key(old_user)
    # if old user had an apikey, we need to copy this to the new user
    if old_user_api_key:
        new_user_api_key = get_api_key(new_user)
        # if new user already have an api key, update the key with old user key
        if new_user_api_key:
            new_user_api_key.key = old_user_api_key.key
            new_user_api_key.save()
        # if new user does not have an api key, change old user apikey to point to new user
        else:
            old_user_api_key.user = new_user
            old_user_api_key.save()


def list_auth_methods(request):
    """Generate a list of authentication methods that request.user uses to
    authenticate to the system and send it back in a HttpResponse.

    :param Request request: the HTTP request object

    :returns: The HttpResponse which contains request.user's list of
        authentication methods
    :rtype: HttpResponse
    """
    userAuthMethodList = []

    # the list of supported non-local DB authentication methods
    supportedAuthMethods = _getSupportedAuthMethods()

    try:
        """
        userProfile = UserProfile.objects.get(user=request.user)

        if userProfile.isDjangoAccount:
            # if the main account for this user is a django account, add his
            # details in the userAuthMethodList (a list of user authentication
            # methods that the user can modify or delete)
            userAuthMethodList.append((request.user.username,
                localdb_auth.auth_display_name, localdb_auth.auth_key))
        """
        # get the user authentication methods for the current user
        userAuths = UserAuthentication.objects.filter(
            userProfile__user=request.user)

        # ... and append it to our list
        for userAuth in userAuths:
            userAuthMethodList.append((userAuth.username,
                                       userAuth.getAuthMethodDescription(),
                                       userAuth.authenticationMethod))

            # also remove the current userAuth from the list of authentication
            # method options that can be added by this user
            del supportedAuthMethods[userAuth.authenticationMethod]

    except UserProfile.DoesNotExist:
        # if there is no userProfile object linked to the current user,
        # he might only have a django account so we'll only add localDB
        # information to the list of user authentication methods he can use
        # to log into the system.
        userAuthMethodList.append((request.user.username,
                                   localdb_auth.auth_display_name, localdb_auth.auth_key))

    LinkedUserAuthenticationForm = \
        createLinkedUserAuthenticationForm(supportedAuthMethods)
    authForm = LinkedUserAuthenticationForm()
    isDjangoAccount = True
    try:
        isDjangoAccount = UserProfile.objects.get(
            user=request.user).isDjangoAccount
    except UserProfile.DoesNotExist:
        isDjangoAccount = True

    c = {'userAuthMethodList': userAuthMethodList,
         'authForm': authForm, 'supportedAuthMethods': supportedAuthMethods,
         'allAuthMethods': _getSupportedAuthMethods(),
         'isDjangoAccount': isDjangoAccount}

    return HttpResponse(render_response_index(request,
                                              'migrate_accounts.html', c))


def openid_migration_method(request):
    migration_form = \
        openid_user_migration_form()
    authForm = migration_form()

    c = {'authForm': authForm, }
    return HttpResponse(render_response_index(request,
                                              'migrate_accounts.html', c))


def confirm_migration(request):
    from tardis.tardis_portal.auth import auth_service
    supportedAuthMethods = _getSupportedAuthMethods()
    migration_form = \
        openid_user_migration_form()
    authForm = migration_form(request.POST)

    if not authForm.is_valid():
        errorMessage = \
            'Please provide all the necessary information to authenticate.'
        return _getJsonFailedResponse(errorMessage)

    # authenticationMethod = authForm.cleaned_data['authenticationMethod']

    # let's try and authenticate here
    authentication_method = 'localdb'
    user = auth_service.authenticate(authMethod=authentication_method,
                                     request=request)

    if user is None:
        errorMessage = 'Wrong username or password. Please try again'
        return _getJsonFailedResponse(errorMessage)

    else:
        data = _setupJsonData(authForm, authentication_method, supportedAuthMethods)
        # return _getJsonSuccessResponse(data)
        return _getJsonConfirmResponse()

def add_auth_method(request):
    """Add a new authentication method to request.user's existing list of
    authentication methods. This method will ask for a confirmation if the user
    wants to merge two accounts if the authentication method he provided
    already exists as a method for another user.

    :param Request request: the HTTP request object

    :returns: The HttpResponse which contains request.user's new list of
        authentication methods
    :rtype: HttpResponse
    """
    from tardis.tardis_portal.auth import auth_service

    supportedAuthMethods = _getSupportedAuthMethods()
    LinkedUserAuthenticationForm = \
        createLinkedUserAuthenticationForm(supportedAuthMethods)
    authForm = LinkedUserAuthenticationForm(request.POST)

    if not authForm.is_valid():
        errorMessage = \
            'Please provide all the necessary information to authenticate.'
        return _getJsonFailedResponse(errorMessage)

    authenticationMethod = authForm.cleaned_data['authenticationMethod']

    # let's try and authenticate here
    user = auth_service.authenticate(authMethod=authenticationMethod,
        request=request)

    if user is None:
        errorMessage = 'Wrong username or password. Please try again'
        return _getJsonFailedResponse(errorMessage)

    # if has already registered to use the provided auth method, then we'll
    # merge the two accounts
    if user != request.user:
        # but before we do that, we'll try and confirm with the user if that's
        # what he really wants
        return _getJsonConfirmResponse()

    # TODO: we'll need to send back a json message with a success status and
    #       other info that can be used to modify the html document

    # get the user authentication methods for the current user
    userAuths = UserAuthentication.objects.filter(
        userProfile__user=request.user)

    # ... and append it to our list
    for userAuth in userAuths:
        # also remove the current userAuth from the list of authentication
        # method options that can be added by this user
        del supportedAuthMethods[userAuth.authenticationMethod]

    data = _setupJsonData(authForm, authenticationMethod, supportedAuthMethods)
    return _getJsonSuccessResponse(data)


def get_api_key(user):
    try:
        apikey = ApiKey.objects.get(user=user)
    except ApiKey.DoesNotExist:
        return None

    return apikey
