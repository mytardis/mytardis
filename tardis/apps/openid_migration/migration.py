import logging

from django.contrib.auth.models import Permission
from django.contrib import messages
from django.conf import settings

from tastypie.models import ApiKey

from tardis.tardis_portal.models import UserProfile, UserAuthentication, \
    ObjectACL, Group
from tardis.tardis_portal.auth.authentication import _getJsonFailedResponse,\
    _getJsonSuccessResponse, _getJsonConfirmResponse

from tardis.tardis_portal.shortcuts import render_response_index
from tardis.apps.openid_migration.models import OpenidUserMigration, OpenidACLMigration

from .tasks import notify_migration_status
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
    supportedAuthMethods = getSupportedAuthMethods()

    # let's try and authenticate here
    user = auth_service.authenticate(authMethod="None", request=request)

    if user is None:
        errorMessage = 'Wrong username or password. Please try again'
        return _getJsonFailedResponse(errorMessage)

    # if has already registered to use the provided auth method, then we can't
    # link the auth method to the user
    if user == request.user:
        errorMessage = "You can't migrate to the same account"
        return _getJsonFailedResponse(errorMessage)

    logger.info("starting migration from %s to %s", user.username,
                request.user.username)
    # check if the "request.user" has a userProfile
    userProfile, created = UserProfile.objects.get_or_create(
        user=request.user)
    # get request user authentication method
    data = _setupJsonData(old_user=user, new_user=request.user)
    # get authenticated user backend
    backend = request.session['_auth_user_backend']
    # get key from backend class name
    auth_provider = get_matching_auth_provider(backend)

    logger.info("linking user authentication")
    # in most of the case it should return one authentication method
    # but in case it returns more than one we need to throw an exception
    # and notify admin about this.
    try:
        userAuths = UserAuthentication.objects.filter(
                    userProfile__user=user)
        if userAuths.count() > 1:
            logger.error("Multiple authentication methods found for user %s" % user)
            return _getJsonFailedResponse("Something went wrong")
        elif userAuths.count() < 1:
            logger.error("No authentication methods found for user %s" % user)
            return _getJsonFailedResponse("Something went wrong")
    except ValueError:
        logger.error("issue with authentication methods for user %s" % user)

    old_authentication_method = userAuths[0].authenticationMethod
    logger.info("Old authentication method is %s", old_authentication_method)

    # let's search for the ACLs that refer to 'user' and transfer them
    # to request.user
    userIdToBeReplaced = user.id
    replacementUserId = request.user.id
    # for logging migration event
    user_migration_record = OpenidUserMigration(
        old_user=user, new_user=request.user,
        old_user_auth_method=old_authentication_method,
        new_user_auth_method=auth_provider[0])
    user_migration_record.save()
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
    user.username = old_username + '_' + old_authentication_method
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
    notify_migration_status.delay(user, old_username, 'AAF')
    logger.info("migration complete")

    message = (
        "Your account has been migrated successfully. "
        "Please note that your source account has been deactivated and no longer accessible. "
        "Please use Login via %s for all of your future logins to %s."
        % (auth_provider[1], getattr(settings, 'SITE_TITLE', 'MyTardis')))
    messages.add_message(request, messages.INFO, message)
    data['auth_method'] = auth_provider[0]
    return _getJsonSuccessResponse(data=data)


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

    new_user.is_superuser = old_user.is_superuser
    new_user.is_staff = old_user.is_staff
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


def openid_migration_method(request):
    migration_form = openid_user_migration_form()
    authForm = migration_form()

    context = dict(
        authForm=authForm,
        site_title=getattr(settings, 'SITE_TITLE', 'MyTardis'),)
    return render_response_index(request, 'migrate_accounts.html', context)


def confirm_migration(request):
    from tardis.tardis_portal.auth import auth_service
    migration_form = \
        openid_user_migration_form()
    authForm = migration_form(request.POST)

    if not authForm.is_valid():
        errorMessage = \
            'Please provide all the necessary information to authenticate.'
        return _getJsonFailedResponse(errorMessage)

    # let's try and authenticate here
    user = auth_service.authenticate(authMethod="None",
                                     request=request)

    if user is None:
        errorMessage = 'Wrong username or password. Please try again'
        return _getJsonFailedResponse(errorMessage)

    # do not allow migration from an inactive account
    if not user.is_active:
        errorMessage = 'Account is inactive'
        return _getJsonFailedResponse(errorMessage)
    # get request user auth method
    backend = request.session['_auth_user_backend']
    # get key from backend class name
    auth_provider = get_matching_auth_provider(backend)
    data = _setupJsonData(user, request.user)
    data['auth_method'] = auth_provider[0]
    return _getJsonConfirmResponse(data)


def _setupJsonData(old_user, new_user):
    """Sets up the JSON data dictionary that will be sent back to the web
    client.
    :param User old_user: the user migrating from
    :param User new_user: the user migrating to
    :returns: The data dictionary
    :rtype: dict
    """
    data = {}
    data['old_username'] = old_user.username
    data['new_username'] = new_user.username
    data['old_user_email'] = old_user.email
    data['new_user_email'] = new_user.email
    logger.debug('Sending partial data to auth methods management page')
    return data


def getSupportedAuthMethods():
    '''Return the list of authentication methods.'''
    # the list of supported non-local DB authentication methods
    supportedAuthMethods = {}

    for authKey, authDisplayName, authBackend in settings.AUTH_PROVIDERS:
        supportedAuthMethods[authKey] = authDisplayName

    return supportedAuthMethods


def get_api_key(user):
    try:
        apikey = ApiKey.objects.get(user=user)
    except ApiKey.DoesNotExist:
        return None

    return apikey


def get_matching_auth_provider(backend):
    for auth_provider in settings.AUTH_PROVIDERS:
        # Each auth provider is a tuple with (key, display name, backend)
        if backend == auth_provider[2]:
            return auth_provider
    return None
