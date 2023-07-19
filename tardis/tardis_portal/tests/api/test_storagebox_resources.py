'''
Testing the StorageBox resources in MyTardis's Tastypie-based REST API

.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import json

from ...models.storage import StorageBox
from . import MyTardisResourceTestCase


class StorageBoxResourceTest(MyTardisResourceTestCase):

    def test_get_storage_box_by_id(self):
        box = StorageBox.get_default_storage()
        expected_output = {
            "id": box.id,
            "name": box.name
        }
        response = self.api_client.get(
            '/api/v1/storagebox/%d/?format=json' % box.id,
            authentication=self.get_admin_credentials())
        self.assertHttpOK(response)
        returned_data = json.loads(response.content.decode())
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)


class StorageBoxOptionResourceTest(MyTardisResourceTestCase):

    def test_get_storage_box_option_by_id(self):
        box = StorageBox.get_default_storage()
        location = box.options.get(key='location')
        expected_output = {
            "id": location.id,
            "key": location.key,
            "value": location.value
        }
        response = self.api_client.get(
            '/api/v1/storageboxoption/%d/?format=json' % location.id,
            authentication=self.get_credentials())
        self.assertHttpOK(response)
        returned_data = json.loads(response.content.decode())
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

    def test_get_storage_box_option_list_from_box_id(self):
        box = StorageBox.get_default_storage()
        location = box.options.get(key='location')
        expected_output = {
            "id": location.id,
            "key": location.key,
            "value": location.value
        }
        response = self.api_client.get(
            '/api/v1/storageboxoption/?storagebox__id=%d&format=json' % box.id,
            authentication=self.get_credentials())
        self.assertHttpOK(response)
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data['meta']['total_count'], 1)
        returned_option = returned_data['objects'][0]
        for key, value in expected_output.items():
            self.assertTrue(key in returned_option)
            self.assertEqual(returned_option[key], value)


class StorageBoxAttributeResourceTest(MyTardisResourceTestCase):

    def test_get_storage_box_attr_list_from_box_id(self):
        box = StorageBox.get_default_storage()
        response = self.api_client.get(
            '/api/v1/storageboxattribute/?storagebox__id=%d&format=json' % box.id,
            authentication=self.get_credentials())
        self.assertHttpOK(response)
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data['meta']['total_count'], 0)
