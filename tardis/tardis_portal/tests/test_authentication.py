'''
Created on 19/01/2011

.. moduleauthor:: Gerson Galang <gerson.galang@versi.edu.au>
'''
import json

from unittest.mock import patch

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Permission


class AuthenticationTestCase(TestCase):

    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username='PUBLIC_USER_TEST')
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        self.client = Client()
        self.loginUrl = "/login/"
        self.manageAuthMethodsUrl = "/accounts/manage_auth_methods/"

        self.user = User.objects.create_user('test', '', 'test')
        self.user.user_permissions.add(Permission.objects.get(codename='change_userauthentication'))

    def testSimpleAuthenticate(self):
        response = self.client.post(self.loginUrl, {'username': 'test',
            'password': 'test', 'authMethod': 'localdb'})
        self.assertEqual(response.status_code, 302)
        self.client.logout()

        # Testing login failures doesn't seem to play well with
        # Django's TransactionTestCase.

        test_login_failures = False
        if test_login_failures:
            response = self.client.post(self.loginUrl, {'username': 'test',
                'password': 'test1', 'authMethod': 'localdb'})
            self.assertEqual(response.context['status'],
                             "Sorry, username and password don't match.")
            self.client.logout()

            response = self.client.post(self.loginUrl, {'username': 'test1',
                'password': 'test', 'authMethod': 'localdb'})
            self.assertEqual(response.context['status'],
                             "Sorry, username and password don't match.")
            self.client.logout()

    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def testManageAuthMethods(self, mock_webpack_get_bundle):
        response = self.client.get(self.manageAuthMethodsUrl)

        # check if the response is a redirect to the login page
        self.assertRedirects(response,
                             '/login/?next=' +
                             self.manageAuthMethodsUrl)

        response = self.client.post(self.loginUrl, {'username': 'test',
            'password': 'test', 'authMethod': 'localdb'})

        response = self.client.get(self.manageAuthMethodsUrl)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)
        self.assertEqual(len(response.context['userAuthMethodList']), 1, response)
        self.assertTrue(response.context['isDjangoAccount'] is True)
        self.assertTrue(len(response.context['supportedAuthMethods']), 1)
        self.assertTrue(len(response.context['allAuthMethods']), 1)

        # let's try and add a new auth method for 'test' user
        response = self.client.post(
            self.manageAuthMethodsUrl, {'operation': 'addAuth',
            'username': 'test@test.com', 'password': 'testpass',
            'authenticationMethod': 'localdb'})

        self.assertTrue(json.loads(response.content.decode())['status'])
        self.client.logout()

    def test_djangoauth(self):
        from django.test.client import RequestFactory
        factory = RequestFactory()

        from ..auth.localdb_auth import DjangoAuthBackend
        dj_auth = DjangoAuthBackend()
        request = factory.post('/login', {'username': 'test',
                                          'password': 'test',
                                          'authMethod': 'localdb'})
        user = dj_auth.authenticate(request)
        self.assertIsInstance(user, User)
