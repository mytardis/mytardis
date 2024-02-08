"""
Testing the Instrument resource in MyTardis's Tastypie-based REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""
import json
from urllib.parse import quote

from django.contrib.auth.models import Group

from ...models.facility import Facility
from ...models.instrument import Instrument
from . import MyTardisResourceTestCase


class InstrumentResourceTest(MyTardisResourceTestCase):
    def test_get_instrument_by_id(self):
        facility_id = Facility.objects.first().id
        group_id = Group.objects.get(name="Test Group").id
        instrument_id = Instrument.objects.first().id
        expected_output = {
            "facility": {
                "manager_group": {
                    "id": group_id,
                    "name": "Test Group",
                    "resource_uri": "/api/v1/group/%d/" % group_id,
                },
                "id": facility_id,
                "name": "Test Facility",
                "resource_uri": "/api/v1/facility/%d/" % facility_id,
                "created_time": "2018-11-29T12:00:00.000000",
                "modified_time": "2018-11-29T12:00:00.000001",
            },
            "id": instrument_id,
            "name": "Test Instrument",
            "resource_uri": "/api/v1/instrument/%d/" % instrument_id,
            "created_time": "2018-11-29T12:00:00.000000",
            "modified_time": "2018-11-29T12:00:00.000001",
        }
        output = self.api_client.get(
            "/api/v1/instrument/%d/" % instrument_id,
            authentication=self.get_credentials(),
        )
        returned_data = json.loads(output.content.decode())
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            if not key.endswith("_time"):
                if isinstance(returned_data[key], dict):
                    for subkey, subvalue in returned_data[key].items():
                        if not subkey.endswith("_time"):
                            self.assertEqual(returned_data[key][subkey], subvalue)
                else:
                    self.assertEqual(returned_data[key], value)

    def test_get_instrument_by_name(self):
        facility_id = Facility.objects.first().id
        group_id = Group.objects.get(name="Test Group").id
        instrument_id = Instrument.objects.first().id
        expected_output = {
            "facility": {
                "manager_group": {
                    "id": group_id,
                    "name": "Test Group",
                    "resource_uri": "/api/v1/group/%d/" % group_id,
                },
                "id": facility_id,
                "name": "Test Facility",
                "resource_uri": "/api/v1/facility/%d/" % facility_id,
                "created_time": "2018-11-29T12:00:00.000000",
                "modified_time": "2018-11-29T12:00:00.000001",
            },
            "id": instrument_id,
            "name": "Test Instrument",
            "resource_uri": "/api/v1/instrument/%d/" % instrument_id,
            "created_time": "2018-11-29T12:00:00.000000",
            "modified_time": "2018-11-29T12:00:00.000001",
        }
        output = self.api_client.get(
            "/api/v1/instrument/?name=%s" % quote(self.testinstrument.name),
            authentication=self.get_credentials(),
        )
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 1)
        returned_object = returned_data["objects"][0]
        for key, value in expected_output.items():
            self.assertTrue(key in returned_object)
            if not key.endswith("_time"):
                if isinstance(returned_object[key], dict):
                    for subkey, subvalue in returned_object[key].items():
                        if not subkey.endswith("_time"):
                            self.assertEqual(returned_object[key][subkey], subvalue)
                else:
                    self.assertEqual(returned_object[key], value)

    def test_post_instrument(self):
        facility_id = Facility.objects.first().id
        post_data = {
            "name": "Another Test Instrument",
            "facility": "/api/v1/facility/%d/" % facility_id,
        }
        instrument_count = Instrument.objects.count()
        self.assertHttpCreated(
            self.api_client.post(
                "/api/v1/instrument/",
                data=post_data,
                authentication=self.get_credentials(),
            )
        )
        self.assertEqual(instrument_count + 1, Instrument.objects.count())

    def test_rename_instrument(self):
        patch_data = {
            "name": "Renamed Test Instrument",
        }
        self.testinstrument.name = "Test Instrument"
        self.testinstrument.save()
        response = self.api_client.patch(
            "/api/v1/instrument/%d/" % self.testinstrument.id,
            data=patch_data,
            authentication=self.get_credentials(),
        )
        self.assertHttpAccepted(response)
        self.testinstrument = Instrument.objects.get(id=self.testinstrument.id)
        self.assertEqual(self.testinstrument.name, "Renamed Test Instrument")

    def test_unauthorized_instrument_access_attempt(self):
        response = self.api_client.get(
            "/api/v1/instrument/%d/" % self.testinstrument.id
        )
        self.assertHttpUnauthorized(response)
