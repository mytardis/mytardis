# -*- coding: utf-8 -*-
"""
test_generate_api_key.py

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
from django.contrib.auth.models import User

from . import ModelTestCase


class ApiKeyTestCase(ModelTestCase):
    def test_create_user_automatically_generate_api_key(self):
        """Verify that create a new user will generate an api_key automatically"""
        user = User.objects.create_user("test", "test@example.com", "passw0rd")
        user.save()

        try:
            api_key = user.api_key
        except:
            api_key = None

        self.assertIsNotNone(api_key)
