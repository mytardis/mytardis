'''
Created on 19/01/2011

@author: gerson
'''
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from tardis.tardis_portal.models import UserAuthentication
from django.utils import simplejson


class AuthenticationTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.loginUrl = "/login/"
        self.manageAuthMethodsUrl = "/accounts/manage_auth_methods/"

        self.user = User.objects.create_user('localdb_test', '', 'test')

    def testSimpleAuthenticate(self):
        response = self.client.post(self.loginUrl, {'username': 'test',
            'password': 'test', 'authMethod': 'localdb'})
        self.assertEqual(response.status_code, 302)
        self.client.logout()

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

    def testCreateNewAccount(self):
        username = 'test@test.com'
        authMethod = 'vbl'
        password = 'testpass'

        userAuth = UserAuthentication.objects.filter(
            username=username, authenticationMethod=authMethod)
        self.assertEqual(userAuth.count(), 0)

        response = self.client.post(self.loginUrl, {'username': username,
            'password': password, 'authMethod': authMethod})

        self.assertEqual(response.status_code, 302)
        userAuth = UserAuthentication.objects.get(
            username=username, authenticationMethod=authMethod)

        self.assertTrue(userAuth is not None)
        self.assertEqual(userAuth.userProfile.user.username, 'vbl_test')

        self.client.logout()

        username = 'test@test1.com'
        authMethod = 'vbl'
        password = 'testpass'

        response = self.client.post(self.loginUrl, {'username': username,
            'password': password, 'authMethod': authMethod})
        self.assertEqual(response.status_code, 500)

        userAuth = UserAuthentication.objects.filter(
            username=username, authenticationMethod=authMethod)
        self.assertEqual(userAuth.count(), 0)
        self.client.logout()

        username = 'test@test.com'
        authMethod = 'vbl'
        password = 'testpasss'

        response = self.client.post(self.loginUrl, {'username': username,
            'password': password, 'authMethod': authMethod})
        self.assertEqual(response.status_code, 500)
        self.client.logout()

    def testManageAuthMethods(self):
        response = self.client.get(self.manageAuthMethodsUrl)

        # check if the response is a redirect to the login page
        self.assertRedirects(response,
                             '/accounts/login/?next=' +
                             self.manageAuthMethodsUrl)

        response = self.client.post(self.loginUrl, {'username': 'test',
            'password': 'test', 'authMethod': 'localdb'})

        response = self.client.get(self.manageAuthMethodsUrl)
        self.assertEqual(len(response.context['userAuthMethodList']), 1)
        self.assertTrue(response.context['isDjangoAccount'] == True)
        self.assertTrue(len(response.context['supportedAuthMethods']), 1)
        self.assertTrue(len(response.context['allAuthMethods']), 1)

        # let's try and add a new auth method for 'test' user
        response = self.client.post(
            self.manageAuthMethodsUrl, {'operation': 'addAuth',
            'username': 'test@test.com', 'password': 'testpass',
            'authenticationMethod': 'vbl'})

        self.assertTrue(simplejson.loads(response.content)['status'])
        self.client.logout()
