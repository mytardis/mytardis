"""
Testing listing all of the endpoints in MyTardis's Tastypie-based REST API

.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""
import json

from . import MyTardisResourceTestCase


class ListEndpointsTest(MyTardisResourceTestCase):
    def test_list_endpoints(self):
        expected_output = {
            "datafileparameter": {
                "list_endpoint": "/api/v1/datafileparameter/",
                "schema": "/api/v1/datafileparameter/schema/",
            },
            "datafileparameterset": {
                "list_endpoint": "/api/v1/datafileparameterset/",
                "schema": "/api/v1/datafileparameterset/schema/",
            },
            "dataset": {
                "list_endpoint": "/api/v1/dataset/",
                "schema": "/api/v1/dataset/schema/",
            },
            "dataset_file": {
                "list_endpoint": "/api/v1/dataset_file/",
                "schema": "/api/v1/dataset_file/schema/",
            },
            "datasetparameter": {
                "list_endpoint": "/api/v1/datasetparameter/",
                "schema": "/api/v1/datasetparameter/schema/",
            },
            "datasetparameterset": {
                "list_endpoint": "/api/v1/datasetparameterset/",
                "schema": "/api/v1/datasetparameterset/schema/",
            },
            "experiment": {
                "list_endpoint": "/api/v1/experiment/",
                "schema": "/api/v1/experiment/schema/",
            },
            "experimentauthor": {
                "list_endpoint": "/api/v1/experimentauthor/",
                "schema": "/api/v1/experimentauthor/schema/",
            },
            "experimentparameter": {
                "list_endpoint": "/api/v1/experimentparameter/",
                "schema": "/api/v1/experimentparameter/schema/",
            },
            "experimentparameterset": {
                "list_endpoint": "/api/v1/experimentparameterset/",
                "schema": "/api/v1/experimentparameterset/schema/",
            },
            "facility": {
                "list_endpoint": "/api/v1/facility/",
                "schema": "/api/v1/facility/schema/",
            },
            "group": {
                "list_endpoint": "/api/v1/group/",
                "schema": "/api/v1/group/schema/",
            },
            "instrument": {
                "list_endpoint": "/api/v1/instrument/",
                "schema": "/api/v1/instrument/schema/",
            },
            "location": {
                "list_endpoint": "/api/v1/location/",
                "schema": "/api/v1/location/schema/",
            },
            "experimentacl": {
                "list_endpoint": "/api/v1/experimentacl/",
                "schema": "/api/v1/experimentacl/schema/",
            },
            "datasetacl": {
                "list_endpoint": "/api/v1/datasetacl/",
                "schema": "/api/v1/datasetacl/schema/",
            },
            "datafileacl": {
                "list_endpoint": "/api/v1/datafileacl/",
                "schema": "/api/v1/datafileacl/schema/",
            },
            "parametername": {
                "list_endpoint": "/api/v1/parametername/",
                "schema": "/api/v1/parametername/schema/",
            },
            "replica": {
                "list_endpoint": "/api/v1/replica/",
                "schema": "/api/v1/replica/schema/",
            },
            "s3utils_replica": {
                "list_endpoint": "/api/v1/s3utils_replica/",
                "schema": "/api/v1/s3utils_replica/schema/",
            },
            "schema": {
                "list_endpoint": "/api/v1/schema/",
                "schema": "/api/v1/schema/schema/",
            },
            "search_advance-search": {
                "list_endpoint": "/api/v1/search_advance-search/",
                "schema": "/api/v1/search_advance-search/schema/",
            },
            "search_search": {
                "list_endpoint": "/api/v1/search_search/",
                "schema": "/api/v1/search_search/schema/",
            },
            "sftp_publickey": {
                "list_endpoint": "/api/v1/sftp_publickey/",
                "schema": "/api/v1/sftp_publickey/schema/",
            },
            "storagebox": {
                "list_endpoint": "/api/v1/storagebox/",
                "schema": "/api/v1/storagebox/schema/",
            },
            "storageboxattribute": {
                "list_endpoint": "/api/v1/storageboxattribute/",
                "schema": "/api/v1/storageboxattribute/schema/",
            },
            "storageboxoption": {
                "list_endpoint": "/api/v1/storageboxoption/",
                "schema": "/api/v1/storageboxoption/schema/",
            },
            "user": {
                "list_endpoint": "/api/v1/user/",
                "schema": "/api/v1/user/schema/",
            },
        }
        response = self.api_client.get("/api/v1/")
        self.assertHttpOK(response)
        returned_data = json.loads(response.content.decode())
        for key, value in expected_output.items():
            self.assertIn(key, returned_data)
            self.assertEqual(returned_data[key], value)
