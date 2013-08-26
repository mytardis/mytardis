from tardis.tardis_portal.auth import auth_service


def getGroups(user):
    return auth_service.getGroups(user)
