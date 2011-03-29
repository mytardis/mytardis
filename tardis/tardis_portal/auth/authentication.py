'''
A module containing helper methods for the manage_auth_methods function in
views.py.

.. moduleauthor:: Gerson Galang <gerson.galang@versi.edu.au>
'''
from django.conf import settings
from django.http import HttpResponse
from django.template import Context

from tardis.tardis_portal.models import UserProfile, UserAuthentication, \
    ExperimentACL, Group
from tardis.tardis_portal.auth import localdb_auth
from tardis.tardis_portal.forms import createLinkedUserAuthenticationForm
from tardis.tardis_portal.shortcuts import render_response_index
from tardis.tardis_portal.logger import logger


def list_auth_methods(request):
    """Generate a list of authentication methods that request.user uses to
    authenticate to the system and send it back in a HttpResponse.

    :param request: the HTTP request object

    :returns: The HttpResponse which contains request.user's list of
        authentication methods

    """
    userAuthMethodList = []

    # the list of supported non-local DB authentication methods
    supportedAuthMethods = _getSupportedAuthMethods()

    try:
        userProfile = UserProfile.objects.get(user=request.user)

        if userProfile.isDjangoAccount:
            # if the main account for this user is a django account, add his
            # details in the userAuthMethodList (a list of user authentication
            # methods that the user can modify or delete)
            userAuthMethodList.append((request.user.username,
                localdb_auth.auth_display_name, localdb_auth.auth_key))

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

    c = Context({'userAuthMethodList': userAuthMethodList,
        'authForm': authForm, 'supportedAuthMethods': supportedAuthMethods,
        'allAuthMethods': _getSupportedAuthMethods(),
        'isDjangoAccount': isDjangoAccount})

    return HttpResponse(render_response_index(request,
                        'tardis_portal/auth_methods.html', c))


def add_auth_method(request):
    """Add a new authentication method to request.user's existing list of
    authentication methods. This method will ask for a confirmation if the user
    wants to merge two accounts if the authentication method he provided
    already exists as a method for another user.

    :param request: the HTTP request object

    :returns: The HttpResponse which contains request.user's new list of
        authentication methods

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


def _setupJsonData(authForm, authenticationMethod, supportedAuthMethods):
    """Sets up the JSON data dictionary that will be sent back to the web
    client.

    :param authForm: the Authentication Form
    :param authenticationMethod: the user's authentication method
    :param supportedAuthMethods: is what's left of the list of authentication
        methods that the user is not using yet

    :returns: The data dictionary

    """
    data = {}
    username = authForm.cleaned_data['username']
    data['username'] = username
    data['authenticationMethod'] = authenticationMethod
    #data['authenticationMethodDesc'] = authenticationMethodDesc

    # flag to tell if there are any more auth methods that we can show
    # the user
    data['supportedAuthMethodsLen'] = len(supportedAuthMethods)

    logger.debug('Sending partial data to auth methods management page')
    return data


def merge_auth_method(request):
    """Merge the account that the user is logged in as and the account that
    he provided in the Authentication Form. Merging accounts involve relinking
    the UserAuthentication table entries, transferring ExperimentACL entries
    to the merged account, changing the Group memberships and deleting the
    unneeded account.

    :param request: the HTTP request object

    :returns: The HttpResponse which contains request.user's new list of
        authentication methods

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

    # if has already registered to use the provided auth method, then we can't
    # link the auth method to the user
    if user != request.user:
        # TODO: find all the experiments "user" has access to and link
        # "request.user" to them

        # check if the "request.user" has a userProfile
        userProfile, created = UserProfile.objects.get_or_create(
            user=request.user)

        # if he has, link 'user's UserAuthentication to it
        userAuths = UserAuthentication.objects.filter(
            userProfile__user=user)

        for userAuth in userAuths:

            userAuth.userProfile = userProfile
            userAuth.save()

            # also remove the current userAuth from the list of authentication
            # method options that can be added by this user
            del supportedAuthMethods[userAuth.authenticationMethod]

        # let's search for the ACLs that refer to 'user' and transfer them
        # to request.user
        userIdToBeReplaced = user.id
        replacementUserId = request.user.id

        # TODO: note that django_user here has been hardcoded. Uli's going
        # to change the implementation on his end so that I can just use a key
        # in here instead of a hardcoded string.
        experimentACLs = ExperimentACL.objects.filter(pluginId='django_user',
            entityId=userIdToBeReplaced)

        for experimentACL in experimentACLs:

            # now let's check if there's already an existing entry in the ACL
            # for the given experiment and replacementUserId
            try:
                acl = ExperimentACL.objects.get(pluginId='django_user',
                    entityId=replacementUserId, experiment=experimentACL.experiment)
                acl.canRead = acl.canRead or experimentACL.canRead
                acl.canWrite = acl.canWrite or experimentACL.canWrite
                acl.canDelete = acl.canDelete or acl.canDelete
                acl.save()
                experimentACL.delete()
            except ExperimentACL.DoesNotExist:
                experimentACL.entityId = replacementUserId
                experimentACL.save()

        # let's also change the group memberships of all the groups that 'user'
        # is a member of
        groups = Group.objects.filter(user=user)
        for group in groups:
            request.user.groups.add(group)

        # we can now delete 'user'
        user.delete()

    data = _setupJsonData(authForm, authenticationMethod, supportedAuthMethods)
    return _getJsonSuccessResponse(data)


def remove_auth_method(request):
    """Removes the non-local DB auth method from the UserAuthentication model.

    :param request: the HTTP request object

    :returns: The HttpResponse which contains request.user's new list of
        authentication methods

    """
    authMethod = request.POST['authMethod']
    try:
        UserAuthentication.objects.get(userProfile__user=request.user,
            authenticationMethod=authMethod).delete()
        return _getJsonSuccessResponse({})

    except UserAuthentication.DoesNotExist:
        return _getJsonFailedResponse(authMethod +
            " auth method you are trying to delete does not exist.")


def edit_auth_method(request):
    '''Change the local DB (Django) password for request.user.'''
    currentPassword = request.POST['currentPassword']
    newPassword = request.POST['newPassword']
    u = request.user
    if (u.check_password(currentPassword)):
        u.set_password(newPassword)
        u.save()
        return _getJsonSuccessResponse()
    else:
        errorMessage = 'The current password you entered is wrong.'
        return _getJsonFailedResponse(errorMessage)


def _getSupportedAuthMethods():
    '''Return the list of all non-local DB authentication methods.'''
    # the list of supported non-local DB authentication methods
    supportedAuthMethods = {}

    for authKey, authDisplayName, authBackend in settings.AUTH_PROVIDERS:
        # we will only add non-localDB authentication methods to the
        # supportedAuthMethods list.
        if authKey != localdb_auth.auth_key:
            supportedAuthMethods[authKey] = authDisplayName

    return supportedAuthMethods


def _getJsonFailedResponse(errorMessage):
    '''Return a failed JSON HttpResponse.'''
    from django.utils import simplejson
    response = {"status": "fail", "errorMessage": errorMessage}
    return HttpResponse(simplejson.dumps(response),
        mimetype="application/json")


def _getJsonSuccessResponse(data={}):
    '''Return a successful JSON HttpResponse.'''
    from django.utils import simplejson
    response = {"status": "success", "data": data}
    return HttpResponse(simplejson.dumps(response),
        mimetype="application/json")


def _getJsonConfirmResponse(data={}):
    '''Return a JSON HttpResponse asking the user for confirmation'''
    from django.utils import simplejson
    response = {"status": "confirm", "data": data}
    return HttpResponse(simplejson.dumps(response),
        mimetype="application/json")
