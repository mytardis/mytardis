from . import auth_service


def getGroups(user):
    return auth_service.getGroups(user)
