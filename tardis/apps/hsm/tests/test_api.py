"""
Testing the hsm app's extensions to the tastypie-based mytardis api
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""
import json
import os

from django.conf import settings

import six

from tardis.tardis_portal.models.access_control import DatasetACL, DatafileACL
from tardis.tardis_portal.models.datafile import DataFile, DataFileObject
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.storage import StorageBox, StorageBoxOption

from tardis.tardis_portal.tests.api import MyTardisResourceTestCase


class HsmAppApiTestCase(MyTardisResourceTestCase):
    def setUp(self):
        super().setUp()
        self.dataset = Dataset.objects.create(description="Test Dataset")
        # self.testexp is defined in MyTardisResourceTestCase
        # and is accessible using self.get_credentials()
        self.dataset.experiments.add(self.testexp)
        if not settings.ONLY_EXPERIMENT_ACLS:
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
        if not settings.ONLY_EXPERIMENT_ACLS:
            self.file_acl = DatafileACL(
                user=self.user,
                datafile=self.datafile,
                isOwner=True,
                canRead=True,
                canDownload=True,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
            self.file_acl.save()
        self.default_storage_box = StorageBox.get_default_storage()
        self.hsm_storage_box = StorageBox.objects.create(
            name="HSM",
            django_storage_class="tardis.apps.hsm.storage.HsmFileSystemStorage",
        )
        self.hsm_location = StorageBoxOption.objects.create(
            storage_box=self.hsm_storage_box,
            key="location",
            value=self.default_storage_box.options.get(key="location").value,
        )
        self.dfo = DataFileObject.objects.create(
            datafile=self.datafile, storage_box=self.default_storage_box
        )
        location = self.dfo.storage_box.options.get(key="location").value
        self.dfo.uri = "test.txt"
        self.dfo.save()
        with open(os.path.join(location, self.dfo.uri), "w") as file_obj:
            file_obj.write("123test\n")

    def tearDown(self):
        self.dataset.delete()
        self.default_storage_box.delete()
        self.hsm_storage_box.delete()

    def test_online_count(self):
        """
        Test counting the number of online files in a dataset

        This method (designed to be fast) looks directly at
        the files on disk without checking if each file is
        verified in the database
        Since the underlying method checks for hidden external attribute on mount.cifs mounted filesystem,
        it may return offline status for a file in test environment
        """
        self.dfo.storage_box = self.hsm_storage_box
        self.dfo.save()
        response = self.api_client.get(
            "/api/v1/hsm_dataset/%s/count/" % self.dataset.id,
            authentication=self.get_credentials(),
        )
        self.assertHttpOK(response)
        expected_output = {"online_files": 0, "total_files": 1}
        returned_data = json.loads(response.content.decode())
        for key, value in six.iteritems(expected_output):
            self.assertIn(key, returned_data)
            self.assertEqual(returned_data[key], value)

    def test_online_check_unverified_file(self):
        """
        Test API endpoint for HSM online check with unverified file
        """
        self.dfo.verified = False
        self.dfo.save()
        response = self.api_client.get(
            "/api/v1/hsm_replica/%s/online/" % self.dfo.id,
            authentication=self.get_credentials(),
        )
        self.assertHttpApplicationError(response)
        data = json.loads(response.content)
        self.assertIn("error_message", data)
        self.assertEqual(
            data["error_message"],
            "Recall failed for DFO %s: %s" % (self.dfo.id, "DataFileObjectNotVerified"),
        )

    def test_online_check_unsupported_storage_class(self):
        """
        Test API endpoint for HSM online check with unsupported storage class
        """
        self.dfo.storage_box = self.default_storage_box
        self.dfo.verified = True
        self.dfo.save()
        response = self.api_client.get(
            "/api/v1/hsm_replica/%s/online/" % self.dfo.id,
            authentication=self.get_credentials(),
        )
        self.assertHttpApplicationError(response)
        data = json.loads(response.content)
        self.assertIn("error_message", data)
        self.assertEqual(
            data["error_message"],
            "Recall failed for DFO %s: %s"
            % (self.dfo.id, "StorageClassNotSupportedError"),
        )

    def test_online_check_valid_storage_class(self):
        """
        Test API endpoint for HSM online check with valid storage class
        """
        self.dfo.storage_box = self.hsm_storage_box
        self.dfo.save()
        response = self.api_client.get(
            "/api/v1/hsm_replica/%s/online/" % self.dfo.id,
            authentication=self.get_credentials(),
        )
        self.assertHttpOK(response)
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data["online"], None)

    def test_online_check_without_acl_access_to_dfo(self):
        """
        Test API endpoint for HSM online check without ACL access to DFO
        """
        # Test 403 forbidden (no ExperimentACL access to dataset):
        self.dataset.experiments.remove(self.testexp)
        if not settings.ONLY_EXPERIMENT_ACLS:
            self.file_acl.delete()
        self.assertHttpForbidden(
            self.api_client.get(
                "/api/v1/hsm_replica/%s/online/" % self.dfo.id,
                authentication=self.get_credentials(),
            )
        )

    def test_online_check_with_bad_password(self):
        """
        Test API endpoint for HSM online check without ACL access to DFO
        """
        # Test 401 unauthorized (wrong password):
        bad_credentials = self.create_basic(  # nosec
            username=self.username, password="wrong pw, dude!"
        )
        self.assertHttpUnauthorized(
            self.api_client.get(
                "/api/v1/hsm_replica/%s/online/" % self.dfo.id,
                authentication=bad_credentials,
            )
        )

    def test_stat_subprocess(self):
        """
        If the Python os.stat function can't determine the number of blocks
        used by the file, then the hsm app falls back to using a subprocess
        """
        from ..utils import _stat_subprocess

        location = self.dfo.storage_box.options.get(key="location").value
        file_path = os.path.join(location, self.dfo.uri)
        size = _stat_subprocess(file_path)[0]
        self.assertEqual(size, self.dfo.datafile.size)

    def test_recall(self):
        """
        Test the API endpoint for recalling a file from tape on an HSM system.
        The "recall" just attempts to read the first bit of the file which on
        most HSM systems will automatically trigger a recall.
        """
        # First test with unverified file which should raise an exception:
        self.dfo.verified = False
        self.dfo.save()
        response = self.api_client.get(
            "/api/v1/hsm_replica/%s/recall/" % self.dfo.id,
            authentication=self.get_credentials(),
        )
        self.assertHttpApplicationError(response)
        data = json.loads(response.content)
        self.assertIn("error_message", data)
        self.assertEqual(
            data["error_message"],
            "Recall failed for DFO %s: %s" % (self.dfo.id, "DataFileObjectNotVerified"),
        )

        # Test with unsupported storage class which should raise an exception:
        self.dfo.storage_box = self.default_storage_box
        self.dfo.verified = True
        self.dfo.save()
        self.assertTrue(DataFileObject.objects.get(id=self.dfo.id).verified)
        response = self.api_client.get(
            "/api/v1/hsm_replica/%s/recall/" % self.dfo.id,
            authentication=self.get_credentials(),
        )
        self.assertHttpApplicationError(response)
        data = json.loads(response.content)
        self.assertIn("error_message", data)
        self.assertEqual(
            data["error_message"],
            "Recall failed for DFO %s: %s"
            % (self.dfo.id, "StorageClassNotSupportedError"),
        )

        # Test with valid HSM storage class:
        self.dfo.storage_box = self.hsm_storage_box
        self.dfo.save()
        # Get fresh DataFile instance to avoid getting cached recall_url:
        datafile = DataFile.objects.get(id=self.dfo.datafile.id)
        expected_recall_url = "/api/v1/hsm_replica/%s/recall/" % self.dfo.id
        self.assertEqual(datafile.recall_url, expected_recall_url)
        response = self.api_client.get(
            "/api/v1/hsm_replica/%s/recall/" % self.dfo.id,
            authentication=self.get_credentials(),
        )
        self.assertHttpOK(response)

        # Now try removing hsm app from installed apps:
        saved_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = [
            app for app in saved_installed_apps if app != "tardis.apps.hsm"
        ]
        # Get fresh DataFile instance to avoid getting cached recall_url:
        datafile = DataFile.objects.get(id=self.dfo.datafile.id)
        self.assertIsNone(datafile.recall_url)
        settings.INSTALLED_APPS = saved_installed_apps

        # Now try simulating not having RECALL_URI_TEMPLATES
        # setting by setting it to its default value:
        settings.RECALL_URI_TEMPLATES = {}
        # Get fresh DataFile instance to avoid getting cached recall_url:
        datafile = DataFile.objects.get(id=self.dfo.datafile.id)
        self.assertIsNone(datafile.recall_url)

        # Test 403 forbidden (no ExperimentACL access to dataset):
        self.dataset.experiments.remove(self.testexp)
        if not settings.ONLY_EXPERIMENT_ACLS:
            self.file_acl.delete()
        self.assertHttpForbidden(
            self.api_client.get(
                "/api/v1/hsm_replica/%s/recall/" % self.dfo.id,
                authentication=self.get_credentials(),
            )
        )

        # Test 401 unauthorized (wrong password):
        bad_credentials = self.create_basic(  # nosec
            username=self.username, password="wrong pw, dude!"
        )
        self.assertHttpUnauthorized(
            self.api_client.get(
                "/api/v1/hsm_replica/%s/recall/" % self.dfo.id,
                authentication=bad_credentials,
            )
        )

    def test_ds_check(self):
        """
        Test the task for updating a dataset's Online Status metadata
        """
        from tardis.tardis_portal.models.parameters import DatasetParameterSet
        from tardis.tardis_portal.models.parameters import Schema
        from ..tasks import ds_check

        # Ensure this dataset's one and only file is in an HSM storage box:
        self.dfo.storage_box = self.hsm_storage_box
        self.dfo.save()

        schema = Schema.objects.get(
            namespace="http://mytardis.org/schemas/hsm/dataset/1"
        )

        self.assertEqual(
            DatasetParameterSet.objects.filter(
                schema=schema, dataset=self.dataset
            ).count(),
            0,
        )

        ds_check(self.dataset.id)

        self.assertEqual(
            DatasetParameterSet.objects.filter(
                schema=schema, dataset=self.dataset
            ).count(),
            1,
        )
