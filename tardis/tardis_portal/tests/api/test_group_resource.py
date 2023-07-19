'''
Testing the Group resource in MyTardis's Tastypie-based REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import json
from urllib.parse import quote

from django.contrib.auth.models import Group

from . import MyTardisResourceTestCase


class GroupResourceTest(MyTardisResourceTestCase):

    def test_get_group_by_id(self):
        group_id = Group.objects.get(name='Test Group').id
        expected_output = {
            "id": group_id,
            "name": "Test Group",
        }
        response = self.api_client.get('/api/v1/group/%d/' % group_id,
                                     authentication=self.get_credentials())
        self.assertHttpOK(response)
        returned_data = json.loads(response.content.decode())
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

    def test_get_group_by_name(self):
        group_id = Group.objects.get(name='Test Group').id
        expected_output = {
            "id": group_id,
            "name": "Test Group",
        }
        response = self.api_client.get(
            '/api/v1/group/?name=%s' % quote(self.testgroup.name),
            authentication=self.get_credentials())
        self.assertHttpOK(response)
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data['meta']['total_count'], 1)
        returned_group = returned_data['objects'][0]
        for key, value in expected_output.items():
            self.assertTrue(key in returned_group)
            self.assertEqual(returned_group[key], value)
