"""
tests/models/__init__.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Mike Laverick <mike.laverick@auckland.ac.nz>

"""
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase


class ModelTestCase(TestCase):
    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        user = "tardis_user1"
        pwd = "secret"
        email = ""
        self.user = User.objects.create_user(user, email, pwd)
