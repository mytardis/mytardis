'''
Testing the s3util app's ability to calculate checksum for S3 objects

.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import unittest
import sys

from mock import patch

from django.test import TestCase

from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.datafile import DataFile, DataFileObject
from tardis.tardis_portal.models.storage import StorageBox, StorageBoxOption


@unittest.skipIf(sys.platform == 'win32',
                 "Windows doesn't have md5sum and sha512sum binaries")
class S3UtilsAppChecksumTestCase(TestCase):
    def setUp(self):
        super(S3UtilsAppChecksumTestCase, self).setUp()
        self.dataset = Dataset.objects.create(description='Test Dataset')
        # Create a DataFile record with the correct size, MD5 sum and
        # SHA 512 sum to represent a file containing the string 'test'
        # without a newline:
        self.datafile = DataFile.objects.create(
            dataset=self.dataset, filename='test.txt', size=4,
            algorithm='md5', checksum='098f6bcd4621d373cade4e832627b4f6')
        self.s3_storage_box = StorageBox.objects.create(
            name='S3 Storage Box',
            django_storage_class='storages.backends.s3boto3.S3Boto3Storage')
        StorageBoxOption.objects.create(
            storage_box=self.s3_storage_box, key='bucket_name',
            value='test-bucket')
        StorageBoxOption.objects.create(
            storage_box=self.s3_storage_box, key='access_key',
            value='mock-access-key')
        StorageBoxOption.objects.create(
            storage_box=self.s3_storage_box, key='secret_key',
            value='mock-secret-key')
        StorageBoxOption.objects.create(
            storage_box=self.s3_storage_box, key='signature_version',
            value='s3')

    def test_checksum(self):
        '''
        Ensure that we can calculate an MD5 sum and a SHA512 sum for
        a file in S3 object storage
        '''
        dfo = DataFileObject(
            storage_box=self.s3_storage_box, datafile=self.datafile)

        def mock_download_fileobj(*args, **kwargs):

            def download(self, uri, pipe):
                pipe.write(b'test')

            return download

        with patch('boto3.s3.inject.bucket_download_fileobj',
                   new_callable=mock_download_fileobj):
            checksum = dfo.calculate_checksum(self.datafile.algorithm)
            self.assertEqual(checksum, self.datafile.checksum)

    def tearDown(self):
        super(S3UtilsAppChecksumTestCase, self).tearDown()
        self.dataset.delete()
        self.s3_storage_box.delete()
