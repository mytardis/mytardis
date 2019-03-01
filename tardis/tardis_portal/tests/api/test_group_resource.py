'''
Testing the Group resource in MyTardis's Tastypie-based REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import json

from django.contrib.auth.models import Group

import six
from six.moves import urllib

from . import MyTardisResourceTestCase


class GroupResourceTest(MyTardisResourceTestCase):

    def test_get_group_by_id(self):
        group_id = Group.objects.get(name='Test Group').id
        expected_output = {
            "id": group_id,
            "name": "Test Group",
        }
        output = self.api_client.get('/api/v1/group/%d/' % group_id,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        for key, value in six.iteritems(expected_output):
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

    def test_get_group_by_name(self):
        group_id = Group.objects.get(name='Test Group').id
        expected_output = {
            "id": group_id,
            "name": "Test Group",
        }
        output = self.api_client.get(
            '/api/v1/group/%d/?name=%s' %
            (group_id, urllib.parse.quote(self.testgroup.name)),
            authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        for key, value in six.iteritems(expected_output):
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)
