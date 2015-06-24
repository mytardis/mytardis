import urllib2

from django.conf import settings

def get_credential_handler():
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    try:
        for url, username, password in settings.REMOTE_SERVER_CREDENTIALS:
            passman.add_password(None, url, username, password)
    except AttributeError:
        # We may not have settings.ATOM_FEED_CREDENTIALS
        pass
    handler = urllib2.HTTPBasicAuthHandler(passman)
    handler.handler_order = 490
    return handler

def get_privileged_opener():
    return urllib2.build_opener(get_credential_handler())
