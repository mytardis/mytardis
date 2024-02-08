"""
Testing the Facility resource in MyTardis's Tastypie-based REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""
import json
from urllib.parse import quote

from django.contrib.auth.models import Group

from ...models.facility import Facility
from . import MyTardisResourceTestCase


class FacilityResourceTest(MyTardisResourceTestCase):
    def test_get_facility_by_id(self):
        first_facility = Facility.objects.first().id
        test_group_id = Group.objects.get(name="Test Group").id
        expected_output = {
            "id": first_facility,
            "manager_group": {
                "id": test_group_id,
                "name": "Test Group",
                "resource_uri": "/api/v1/group/%d/" % test_group_id,
            },
            "name": "Test Facility",
            "resource_uri": "/api/v1/facility/%d/" % first_facility,
        }
        output = self.api_client.get(
            "/api/v1/facility/%d/" % first_facility,
            authentication=self.get_credentials(),
        )
        returned_data = json.loads(output.content.decode())
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

    def test_get_facility_by_name(self):
        first_facility = Facility.objects.first().id
        test_group_id = Group.objects.get(name="Test Group").id
        expected_output = {
            "id": first_facility,
            "manager_group": {
                "id": test_group_id,
                "name": "Test Group",
                "resource_uri": "/api/v1/group/%d/" % test_group_id,
            },
            "name": "Test Facility",
            "resource_uri": "/api/v1/facility/%d/" % first_facility,
        }
        output = self.api_client.get(
            "/api/v1/facility/?name=%s" % quote(self.testfacility.name),
            authentication=self.get_credentials(),
        )
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 1)
        returned_object = returned_data["objects"][0]
        for key, value in expected_output.items():
            self.assertTrue(key in returned_object)
            self.assertEqual(returned_object[key], value)

    def test_get_facility_by_manager_group_id(self):
        """This type of query can be used to iterate through a user's groups,
        and use each group's id to determine which facilities a user
        manages, i.e. a way to obtain the functionality implemented by
        :func:`~tardis.tardis_portal.models.facility.facilities_managed_by`
        via the API
        """

        facility_id = Facility.objects.first().id
        group_id = Group.objects.get(name="Test Group").id
        expected_output = {
            "manager_group": {
                "id": group_id,
                "name": "Test Group",
                "resource_uri": "/api/v1/group/%d/" % group_id,
            },
            "id": facility_id,
            "name": "Test Facility",
            "resource_uri": "/api/v1/facility/%d/" % facility_id,
        }
        output = self.api_client.get(
            "/api/v1/facility/?manager_group__id=%d" % group_id,
            authentication=self.get_credentials(),
        )
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 1)
        returned_object = returned_data["objects"][0]
        for key, value in expected_output.items():
            self.assertTrue(key in returned_object)
            self.assertEqual(returned_object[key], value)
