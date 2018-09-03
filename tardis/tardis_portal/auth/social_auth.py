from django.conf import settings
from django.http import HttpResponse

from tardis.tardis_portal.models import UserAuthentication
from django.contrib.auth.models import Permission


def add_authentication_method(**kwargs):
    """Creates an authentication record for OPenID authenticated user"""
    #add authentication method only if is a new user
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
                                            authenticationMethod=authMethod)
        authentication.save()
        kwargs['authentication'] = authentication
    except:
        pass
    return kwargs


def get_auth_method(authenticatedBackendName):
    """Return matching user authentication method from list of authentication methods in settings"""

    for authKey, authDisplayName, authBackend in settings.AUTH_PROVIDERS:
        authBackendClassName = authBackend.split('.')[-1]
        if authBackendClassName == authenticatedBackendName:
            return authKey


def add_user_permissions(**kwargs):
    """Adds default permission to OPenID authenticated user"""
    user = kwargs.get('user')
    user.user_permissions.add(Permission.objects.get(codename='add_experiment'))
    user.user_permissions.add(Permission.objects.get(codename='change_experiment'))
    user.user_permissions.add(Permission.objects.get(codename='change_group'))
    user.user_permissions.add(Permission.objects.get(codename='change_userauthentication'))
    user.user_permissions.add(Permission.objects.get(codename='change_objectacl'))
    user.user_permissions.add(Permission.objects.get(codename='add_datafile'))
    user.user_permissions.add(Permission.objects.get(codename='change_dataset'))

    return kwargs

def require_approval(**kwargs):
    '''
    :param kwargs:
    :return:
    '''

    isNewUser = kwargs.get('is_new')
    if not isNewUser:
        return None

    authentication = kwargs.get('authentication')
    authentication.approved = False
    authentication.save()
    return kwargs
