"""
Tests related to OpenID migration views
"""
from unittest.mock import patch

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.test.client import Client


class OpenIDMigrationViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # old_user
        user_old_username = "tardis_user1"
        # new_user
        user_new_username = "tardis_user2"
        pwd = "secret"
        email = "tadis@tardis.com"
        self.user_new = User.objects.create_user(user_new_username, email, pwd)
        self.user_old = User.objects.create_user(user_old_username, email, pwd)
        # add permission
        self.user_new.user_permissions.add(
            Permission.objects.get(codename="add_openidusermigration")
        )

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_migrate_accounts(self, mock_webpack_get_bundle):
        client = Client()
        response = client.get("/apps/openid-migration/migrate-accounts/")

        self.assertEqual(response.status_code, 302)
        login = client.login(username=self.user_new.username, password="secret")
        self.assertTrue(login)
        response = client.get("/apps/openid-migration/migrate-accounts/")

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)
