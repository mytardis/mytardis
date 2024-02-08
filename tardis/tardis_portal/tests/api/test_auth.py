"""
Testing authentication and authorization in the Tastypie-based
MyTardis REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""
from django.test import TestCase

from . import MyTardisResourceTestCase


class ACLAuthorizationTest(TestCase):
    pass


class MyTardisAuthenticationTest(MyTardisResourceTestCase):
    def test_bad_credentials(self):
        self.assertHttpOK(self.api_client.get("/api/v1/experiment/"))
        good_credentials = self.create_basic(
            username=self.username, password=self.password
        )
        bad_credentials = self.create_basic(
            username=self.username, password="wrong pw, dude!"  # nosec
        )
        self.assertHttpOK(
            self.api_client.get("/api/v1/experiment/", authentication=good_credentials)
        )
        self.assertHttpUnauthorized(
            self.api_client.get("/api/v1/experiment/", authentication=bad_credentials)
        )

    def test_apikey_authentication(self):
        good_credentials = self.get_apikey_credentials()
        bad_credentials = self.create_apikey(
            username=self.username, api_key="wrong api_key"
        )
        # Test api_key authentication
        self.assertHttpOK(
            self.api_client.get("/api/v1/experiment/", authentication=good_credentials)
        )
        self.assertHttpUnauthorized(
            self.api_client.get("/api/v1/experiment/", authentication=bad_credentials)
        )
