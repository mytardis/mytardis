from django.contrib.auth.models import User
from django.test import TestCase

from ..models import OpenidUserMigration


class ModelTestCase(TestCase):
    def setUp(self):
        self.old_user = User.objects.create_user(
            "abc", email="abc@example.com", password="abc"
        )
        self.new_user = User.objects.create_user(
            "def", email="def@example.com", password="def"
        )

    def create_OpenidUserMigration(self):

        return OpenidUserMigration.objects.create(
            old_user=self.old_user,
            new_user=self.new_user,
            old_user_auth_method="ldap",
            new_user_auth_method="AAF",
        )

    def test_OpenidUserMigration_creation(self):
        openidUserMigration_obj = self.create_OpenidUserMigration()
        self.assertTrue(isinstance(openidUserMigration_obj, OpenidUserMigration))
        self.assertEqual(str(openidUserMigration_obj), "abc | def")
