'''
Created on 14/01/2011

@author: gerson
'''
from django.http import HttpResponse
from tardis.tardis_portal.models import *
from tardis.tardis_portal.auth import localdb_auth
from tardis.tardis_portal.forms import createLinkedUserAuthenticationForm
from django.template import Context
from tardis.tardis_portal.shortcuts import *
from tardis.tardis_portal.logger import logger

def list_auth_methods(request):
    userAuthMethodList = []
        
    # the list of supported non-local DB authentication methods
    supportedAuthMethods = _getSupportedAuthMethods()

    try:
        userProfile = UserProfile.objects.get(user=request.user)

        if not userProfile.isNotADjangoAccount:
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
    print "yes", UserProfile.objects.get(user=request.user).isNotADjangoAccount
    
    c = Context({'userAuthMethodList': userAuthMethodList,
        'authForm': authForm, 'supportedAuthMethods': supportedAuthMethods,
        'allAuthMethods': _getSupportedAuthMethods(),
        'isNotDjangoAccount': UserProfile.objects.get(user=request.user).isNotADjangoAccount})

    return HttpResponse(render_response_index(request,
                        'tardis_portal/auth_methods.html', c))

def add_auth_method(request):
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
        errorMessage = 'Sorry, that user account already exists in the system'
        return _getJsonFailedResponse(errorMessage)

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
            
    data= {}
    username = authForm.cleaned_data['username']
    data['username'] = username
    data['authenticationMethod'] = authenticationMethod
    #data['authenticationMethodDesc'] = authenticationMethodDesc
    
    # flag to tell if there are any more auth methods that we can show
    # the user
    data['supportedAuthMethodsLen'] = len(supportedAuthMethods)

    logger.debug('Sending partial data to auth methods management page')
    return _getJsonSuccessResponse(data)


def remove_auth_method(request):
    """Removes the non-local DB auth method from the UserAuthentication model.
    
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
    # the list of supported non-local DB authentication methods
    supportedAuthMethods = {}

    for authKey, authDisplayName, authBackend  in settings.AUTH_PROVIDERS:
        # we will only add non-localDB authentication methods to the 
        # supportedAuthMethods list.
        if authKey != localdb_auth.auth_key:
            supportedAuthMethods[authKey] = authDisplayName
    
    return supportedAuthMethods        


def _getJsonFailedResponse(errorMessage):
    from django.utils import simplejson
    response = {"status": "fail", "errorMessage": errorMessage}
    return HttpResponse(simplejson.dumps(response),
        mimetype="application/json")


def _getJsonSuccessResponse(data={}):
    from django.utils import simplejson
    response = {"status": "success", "data": data}
    return HttpResponse(simplejson.dumps(response),
        mimetype="application/json")
