'''
Testing the hsm app's extensions to the tastypie-based mytardis api
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import json
import os

import six

from tardis.tardis_portal.models.datafile import DataFile, DataFileObject
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.storage import StorageBox

from tardis.tardis_portal.tests.test_api import MyTardisResourceTestCase


class HsmAppApiTestCase(MyTardisResourceTestCase):
    def setUp(self):
        super(HsmAppApiTestCase, self).setUp()
        self.dataset = Dataset.objects.create(description='Test Dataset')
        # self.testexp is defined in MyTardisResourceTestCase
        # and is accessible using self.get_credentials()
        self.dataset.experiments.add(self.testexp)
        self.datafile = DataFile.objects.create(
            dataset=self.dataset, filename='test.txt',
            size=8, md5sum="930e419034038dfad994f0d2e602146c")
        self.storage_box = StorageBox.get_default_storage()
        self.dfo = DataFileObject.objects.create(
            datafile=self.datafile, storage_box=self.storage_box)
        location = self.storage_box.options.get(key='location').value
        self.dfo.uri = "test.txt"
        self.dfo.save()
        with open(os.path.join(location, self.dfo.uri), 'w') as file_obj:
            file_obj.write("123test\n")

    def test_online_count(self):
        '''
        Test counting the number of online files in a dataset

        This method (designed to be fast) looks directly at
        the files on disk without checking if each file is
        verified in the database
        '''
        self.storage_box.django_storage_class = \
            'tardis.apps.hsm.storage.HsmFileSystemStorage'
        self.storage_box.save()
        response = self.api_client.get(
            '/api/v1/hsm_dataset/%s/count/' % self.dataset.id,
             authentication=self.get_credentials())
        self.assertHttpOK(response)
        expected_output = {
            "online_files": 1,
            "total_files": 1
        }
        returned_data = json.loads(response.content)
        for key, value in six.iteritems(expected_output):
            self.assertIn(key, returned_data)
            self.assertEqual(returned_data[key], value)


    def test_online_check(self):
        '''
        Test the API endpoint for checking the online status of a file on
        a Hierarchical Storage Management (HSM) system
        '''
        from tardis.apps.hsm.check import DataFileObjectNotVerified
        from tardis.apps.hsm.check import StorageClassNotSupportedError

        # First test with unverified file which should raise an exception:
        self.dfo.verified = False
        self.dfo.save()
        with self.assertRaises(DataFileObjectNotVerified):
            self.api_client.get(
                '/api/v1/hsm_replica/%s/online/' % self.dfo.id,
                 authentication=self.get_credentials())

        # Test with unsupported storage class which should raise an exception:
        self.dfo.verified = True
        self.dfo.save()
        self.assertEqual(
            self.storage_box.django_storage_class,
            'tardis.tardis_portal.storage.MyTardisLocalFileSystemStorage')
        with self.assertRaises(StorageClassNotSupportedError):
            self.api_client.get(
                '/api/v1/hsm_replica/%s/online/' % self.dfo.id,
                 authentication=self.get_credentials())

        # Test with valid HSM storage class:
        self.storage_box.django_storage_class = \
            'tardis.apps.hsm.storage.HsmFileSystemStorage'
        self.storage_box.save()
        response = self.api_client.get(
            '/api/v1/hsm_replica/%s/online/' % self.dfo.id,
             authentication=self.get_credentials())
        self.assertHttpOK(response)
        expected_output = {
            "online": True,
        }
        returned_data = json.loads(response.content)
        for key, value in six.iteritems(expected_output):
            self.assertIn(key, returned_data)
            self.assertEqual(returned_data[key], value)

        # Test 403 forbidden (no ObjectACL access to dataset):
        self.dataset.experiments.remove(self.testexp)
        self.assertHttpForbidden(self.api_client.get(
            '/api/v1/hsm_replica/%s/online/' % self.dfo.id,
             authentication=self.get_credentials()))

        # Test 401 unauthorized (wrong password):
        bad_credentials = self.create_basic(
            username=self.username, password="wrong pw, dude!")
        self.assertHttpUnauthorized(self.api_client.get(
            '/api/v1/hsm_replica/%s/online/' % self.dfo.id,
             authentication=bad_credentials))

    def test_stat_subprocess(self):
        '''
        If the Python os.stat function can't determine the number of blocks
        used by the file, then the hsm app falls back to using a subprocess
        '''
        from ..utils import _stat_subprocess
        location = self.storage_box.options.get(key='location').value
        file_path = os.path.join(location, self.dfo.uri)
        size, blocks = _stat_subprocess(file_path)
        self.assertEqual(size, self.dfo.datafile.size)

    def test_recall(self):
        '''
        Test the API endpoint for recalling a file from tape on an HSM system.
        The "recall" just attempts to read the first bit of the file which on
        most HSM systems will automatically trigger a recall.
        '''
        from tardis.apps.hsm.check import DataFileObjectNotVerified
        from tardis.apps.hsm.check import StorageClassNotSupportedError

        # First test with unverified file which should raise an exception:
        self.dfo.verified = False
        self.dfo.save()
        with self.assertRaises(DataFileObjectNotVerified):
            self.api_client.get(
                '/api/v1/hsm_replica/%s/recall/' % self.dfo.id,
                 authentication=self.get_credentials())

        # Test with unsupported storage class which should raise an exception:
        self.dfo.verified = True
        self.dfo.save()
        self.assertEqual(
            self.storage_box.django_storage_class,
            'tardis.tardis_portal.storage.MyTardisLocalFileSystemStorage')
        with self.assertRaises(StorageClassNotSupportedError):
            self.api_client.get(
                '/api/v1/hsm_replica/%s/recall/' % self.dfo.id,
                 authentication=self.get_credentials())

        # Test with valid HSM storage class:
        self.storage_box.django_storage_class = \
            'tardis.apps.hsm.storage.HsmFileSystemStorage'
        self.storage_box.save()
        response = self.api_client.get(
            '/api/v1/hsm_replica/%s/recall/' % self.dfo.id,
             authentication=self.get_credentials())
        self.assertHttpOK(response)

        # Test 403 forbidden (no ObjectACL access to dataset):
        self.dataset.experiments.remove(self.testexp)
        self.assertHttpForbidden(self.api_client.get(
            '/api/v1/hsm_replica/%s/recall/' % self.dfo.id,
             authentication=self.get_credentials()))

        # Test 401 unauthorized (wrong password):
        bad_credentials = self.create_basic(
            username=self.username, password="wrong pw, dude!")
        self.assertHttpUnauthorized(self.api_client.get(
            '/api/v1/hsm_replica/%s/recall/' % self.dfo.id,
             authentication=bad_credentials))

    def test_ds_check(self):
        '''
        Test the task for updating a dataset's Online Status metadata
        '''
        from tardis.tardis_portal.models.parameters import DatasetParameterSet
        from tardis.tardis_portal.models.parameters import Schema
        from ..tasks import ds_check

        self.storage_box.django_storage_class = \
            'tardis.apps.hsm.storage.HsmFileSystemStorage'
        self.storage_box.save()

        schema = Schema.objects.get(
            namespace='http://mytardis.org/schemas/hsm/dataset/1')

        self.assertEqual(
            DatasetParameterSet.objects.filter(
                schema=schema, dataset=self.dataset).count(),
            0)

        ds_check(self.dataset.id)

        self.assertEqual(
            DatasetParameterSet.objects.filter(
                schema=schema, dataset=self.dataset).count(),
            1)
