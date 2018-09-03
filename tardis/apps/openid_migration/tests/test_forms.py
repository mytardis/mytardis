'''
Tests related to OpenID migration forms
'''

from django.test import TestCase
from django.contrib.auth.models import User

from ..forms import openid_user_migration_form


class OpenIDMigrationFormTestCase(TestCase):
    def setUp(self):
        user_new_username = 'tardis_user2'
        pwd = 'secret'
        email = 'tadis@tardis.com'
        self.user_new = User.objects.create_user(user_new_username, email, pwd)

    def test_init(self):
        form = openid_user_migration_form()

    # TODO: Test valid data
    # def test_valid_data(self):
