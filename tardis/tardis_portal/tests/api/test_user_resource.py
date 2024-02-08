"""
Testing the User resource in MyTardis's Tastypie-based REST API

.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""
import json
from urllib.parse import quote

from . import MyTardisResourceTestCase


class UserResourceTest(MyTardisResourceTestCase):
    def test_get_user_by_id(self):
        expected_output = {
            "id": self.user.id,
            "first_name": "Testing",
            "last_name": "MyTardis API",
        }
        response = self.api_client.get(
            "/api/v1/user/%d/" % self.user.id,
            authentication=self.get_admin_credentials(),
        )
        self.assertHttpOK(response)
        returned_data = json.loads(response.content.decode())
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

    def test_get_user_by_username(self):
        expected_output = {"id": self.user.id, "username": self.user.username}
        response = self.api_client.get(
            "/api/v1/user/?username=%s" % quote(self.user.username),
            authentication=self.get_credentials(),
        )
        self.assertHttpOK(response)
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 1)
        returned_user = returned_data["objects"][0]
        for key, value in expected_output.items():
            self.assertTrue(key in returned_user)
            self.assertEqual(returned_user[key], value)
