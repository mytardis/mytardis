'''
Created on Dec 15, 2011

@author: uqtdettr
'''

import urllib2
from django.conf import settings
from django.contrib.auth.models import User
from tardis.tardis_portal.auth.interfaces import AuthProvider

class HttpBasicEndpointAuth(AuthProvider):
    '''
    This class provides authentication against a HTTP resource protected by
    HTTP Basic authentication. Access is granted based on the user credentials
    being valid against that resource.
    '''

    class SimplePasswordMgr(urllib2.HTTPPasswordMgr):
        '''
        Simple password manager which provides the same credentials, no matter
        the realm or the uri.
        '''

        def __init__(self):
            self.clear()

        def add_password(self, realm, uri, username, password):
            self.credentials = (username, password)

        def find_user_password(self, realm, authuri):
            return self.credentials

        def clear(self):
            self.credentials = (None, None)


    def __init__(self,openerDirector = urllib2.build_opener(), endpoint=None):
        self.passman = self.SimplePasswordMgr()
        openerDirector.add_handler(urllib2.HTTPBasicAuthHandler(self.passman))
        self.openerDirector = openerDirector
        self.endpoint = endpoint or settings.HTTP_BASIC_AUTH_ENDPOINT

    def authenticate(self, request):
        """ Authenticate a user, expecting the user will be using
        form-based auth and the *username* and *password* will be
        passed in url-encoded form **POST** variables.

        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`
        """
        username = request.POST['username']
        password = request.POST['password']
        if self._openEndpointWithCredentials(username, password) == None:
            return None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username, '')
            user.save()
        # We don't want a localdb user created, so don't use a dict
        return user

    def get_user(self, user_id):
        raise NotImplemented()

    def _set_password(self, username, password):
        self.passman.clear()
        self.passman.add_password(None, None, username, password)

    def _openEndpointWithCredentials(self,username,password):
        self._set_password(username, password)
        try:
            result = self.openerDirector.open(self.endpoint)
            return result
        except urllib2.HTTPError:
            return None