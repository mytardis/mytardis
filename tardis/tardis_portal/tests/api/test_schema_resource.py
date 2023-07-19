'''
Testing the Schema resource in MyTardis's Tastypie-based REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>

'''
import json
from urllib.parse import quote

from ...models.parameters import Schema
from . import MyTardisResourceTestCase


class SchemaResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super().setUp()
        self.test_schema = Schema.objects.create(
	    namespace="http://schema.namespace",
	    type=Schema.DATAFILE)

    def tearDown(self):
        self.test_schema.delete()

    def test_get_schema_by_id(self):
        expected_output = {
            "id": self.test_schema.id,
            "namespace": "http://schema.namespace"
        }
        response = self.api_client.get(
            '/api/v1/schema/%d/' % self.test_schema.id,
            authentication=self.get_admin_credentials())
        self.assertHttpOK(response)
        returned_data = json.loads(response.content.decode())
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

    def test_get_schema_by_namespace(self):
        expected_output = {
            "id": self.test_schema.id,
            "namespace": self.test_schema.namespace
        }
        response = self.api_client.get(
            '/api/v1/schema/?namespace=%s&format=json'
            % quote(self.test_schema.namespace),
            authentication=self.get_admin_credentials())
        self.assertHttpOK(response)
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data['meta']['total_count'], 1)
        returned_object = returned_data['objects'][0]
        for key, value in expected_output.items():
            self.assertTrue(key in returned_object)
            self.assertEqual(returned_object[key], value)
