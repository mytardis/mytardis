"""
Testing the s3util app's extensions to the tastypie-based mytardis api

.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""
from unittest.mock import patch

import botocore.signers

from django.conf import settings

from tardis.tardis_portal.tests.api import MyTardisResourceTestCase

from tardis.tardis_portal.models.access_control import DatasetACL, DatafileACL
from tardis.tardis_portal.models.datafile import DataFile, DataFileObject
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.storage import StorageBox, StorageBoxOption


class S3UtilsAppApiTestCase(MyTardisResourceTestCase):
    def setUp(self):
        super().setUp()
        self.dataset = Dataset.objects.create(description="Test Dataset")
        # self.testexp is defined in MyTardisResourceTestCase
        # and is accessible using self.get_credentials()
        self.dataset.experiments.add(self.testexp)
        if not settings.settings.ONLY_EXPERIMENT_ACLS:
            self.set_acl = DatasetACL(
                user=self.user,
                dataset=self.dataset,
                isOwner=True,
                canRead=True,
                canDownload=True,
                aclOwnershipType=DatasetACL.OWNER_OWNED,
            )
            self.set_acl.save()
        self.datafile = DataFile.objects.create(
            dataset=self.dataset,
            filename="test.txt",
            size=8,
            md5sum="930e419034038dfad994f0d2e602146c",
        )
        if not settings.settings.ONLY_EXPERIMENT_ACLS:
            self.file_acl = DatafileACL(
                user=self.user,
                datafile=self.datafile,
                isOwner=True,
                canRead=True,
                canDownload=True,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
            self.file_acl.save()
        self.s3_storage_box = StorageBox.objects.create(
            name="S3 Storage Box",
            django_storage_class="storages.backends.s3boto3.S3Boto3Storage",
        )
        StorageBoxOption.objects.create(
            storage_box=self.s3_storage_box, key="bucket_name", value="s3-mock-bucket"
        )
        StorageBoxOption.objects.create(
            storage_box=self.s3_storage_box,
            key="endpoint_url",
            value="http://169.254.169.254",
        )
        StorageBoxOption.objects.create(
            storage_box=self.s3_storage_box, key="access_key", value="mock-access-key"
        )
        StorageBoxOption.objects.create(
            storage_box=self.s3_storage_box, key="secret_key", value="mock-secret-key"
        )
        StorageBoxOption.objects.create(
            storage_box=self.s3_storage_box, key="signature_version", value="s3"
        )

        def mock_verify(*args, **kwargs):
            return True

        with patch.object(DataFileObject, "verify", mock_verify):
            self.dfo = DataFileObject.objects.create(
                datafile=self.datafile, storage_box=self.s3_storage_box
            )

        self.original_generate_presigned_url = botocore.signers.generate_presigned_url

        def mock_generate_presigned_url(*args, **kwargs):
            return "https://presigned.url/"

        botocore.signers.generate_presigned_url = mock_generate_presigned_url

    def tearDown(self):
        botocore.signers.generate_presigned_url = self.original_generate_presigned_url
        self.dataset.delete()
        self.s3_storage_box.delete()

    def test_download_dfo(self):
        """
        Test downloading a DataFileObject using the s3util app's extensions
        to the MyTardis REST API.
        """
        # First test with valid credentials:
        response = self.api_client.get(
            "/api/v1/s3utils_replica/%s/download/" % self.dfo.id,
            authentication=self.get_credentials(),
        )
        self.assertEqual(response.status_code, 302)

        # Now test without valid credentials:
        response = self.api_client.get(
            "/api/v1/s3utils_replica/%s/download/" % self.dfo.id
        )
        self.assertEqual(response.status_code, 403)
