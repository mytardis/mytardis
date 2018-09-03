'''
Tests related to OpenID migration views
'''

from compare import expect

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Permission
from django.http import HttpRequest, QueryDict

from ..views import migrate_accounts


class OpenIDMigrationViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # old_user
        user_old_username = 'tardis_user1'
        # new_user
        user_new_username = 'tardis_user2'
        pwd = 'secret'
        email = 'tadis@tardis.com'
        self.user_new = User.objects.create_user(user_new_username, email, pwd)
        self.user_old = User.objects.create_user(user_old_username, email, pwd)
        # add permission
        self.user_new.user_permissions.add(Permission.objects.get(codename='change_userauthentication'))

    def test_migrate_accounts(self):
        client = Client()
        response = client.get('/apps/openid-migration/migrate-accounts/')
        expect(response.status_code).to_equal(302)
        login = client.login(username=self.user_new.username, password='secret')
        self.assertTrue(login)
        response = client.get('/apps/openid-migration/migrate-accounts/')
        expect(response.status_code).to_equal(200)

