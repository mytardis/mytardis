"""
Testing the Dataset resource in MyTardis's Tastypie-based REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""

import json

from django.contrib.auth.models import User
from django.test import override_settings
from urllib.parse import quote

from ...models.access_control import ExperimentACL, DatasetACL, DatafileACL
from ...models.datafile import DataFile
from ...models.dataset import Dataset
from ...models.experiment import Experiment
from ...models.instrument import Instrument

from . import MyTardisResourceTestCase


class DatasetResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super().setUp()
        self.exp = Experiment(
            title="test exp", institution_name="monash", created_by=self.user
        )
        self.exp.save()
        self.extra_instrument = Instrument()
        self.extra_instrument = Instrument(
            name="Extra Instrument", facility=self.testfacility
        )
        self.extra_instrument.save()
        self.ds_no_instrument = Dataset()
        self.ds_no_instrument.description = "Dataset no instrument"
        self.ds_no_instrument.save()
        self.ds_no_instrument.experiments.add(self.testexp)
        self.ds_with_instrument = Dataset()
        self.ds_with_instrument.description = "Dataset with instrument"
        self.ds_with_instrument.instrument = self.testinstrument
        self.ds_with_instrument.save()
        self.ds_with_instrument.experiments.add(self.testexp)
        self.ds_with_instrument2 = Dataset()
        self.ds_with_instrument2.description = "Dataset with a different instrument"
        self.ds_with_instrument2.instrument = self.extra_instrument
        self.ds_with_instrument2.save()
        self.ds_with_instrument2.experiments.add(self.testexp)

    def test_get_dataset_no_instrument(self):
        uri = "/api/v1/dataset/?description=%s" % quote(
            self.ds_no_instrument.description
        )
        output = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 1)
        returned_object = returned_data["objects"][0]
        self.assertTrue("description" in returned_object)
        self.assertEqual(
            returned_object["description"], self.ds_no_instrument.description
        )
        self.assertTrue("instrument" in returned_object)
        self.assertIsNone(returned_object["instrument"])

    def test_get_dataset_with_instrument(self):
        uri = "/api/v1/dataset/?description=%s" % quote(
            self.ds_with_instrument.description
        )
        output = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 1)
        returned_object = returned_data["objects"][0]
        self.assertTrue("description" in returned_object)
        self.assertEqual(
            returned_object["description"], self.ds_with_instrument.description
        )
        self.assertTrue("instrument" in returned_object)
        self.assertTrue("id" in returned_object["instrument"])
        self.assertEqual(returned_object["instrument"]["id"], self.testinstrument.id)

    def test_get_dataset_filter_instrument(self):
        uri = "/api/v1/dataset/?instrument=%s" % self.extra_instrument.id
        output = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 1)
        returned_object = returned_data["objects"][0]
        self.assertTrue("instrument" in returned_object)
        self.assertTrue("id" in returned_object["instrument"])
        self.assertEqual(returned_object["instrument"]["id"], self.extra_instrument.id)

    def test_post_dataset(self):
        exp_id = Experiment.objects.first().id
        post_data = {
            "description": "api test dataset",
            "experiments": [
                "/api/v1/experiment/%d/" % exp_id,
            ],
            "immutable": False,
        }
        dataset_count = Dataset.objects.count()
        response = self.api_client.post(
            "/api/v1/dataset/", data=post_data, authentication=self.get_credentials()
        )
        self.assertHttpCreated(response)
        self.assertEqual(dataset_count + 1, Dataset.objects.count())
        created_dataset_uri = response["Location"]
        created_dataset_id = created_dataset_uri.split("/")[-2]
        created_dataset = Dataset.objects.get(id=created_dataset_id)
        self.assertEqual(created_dataset.experiments.count(), 1)
        self.assertEqual(created_dataset.experiments.first().id, exp_id)

    def test_get_dataset_files(self):
        ds_id = self.ds_no_instrument.id
        uri = "/api/v1/dataset/%d/files/" % ds_id
        response = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 0)

    def test_get_root_dir_nodes(self):
        dataset = Dataset.objects.create(
            description="test dataset",
        )
        dataset.experiments.add(self.testexp)
        dataset.save()
        uri = "/api/v1/dataset/%d/root-dir-nodes/" % dataset.id
        response = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data, [{"next_page": False}])

        DataFile.objects.create(
            dataset=dataset,
            filename="filename2",
            size=0,
            md5sum="bogus",
            directory="subdir",
        )
        df1 = DataFile.objects.create(
            dataset=dataset, filename="filename1", size=0, md5sum="bogus"
        )

        response = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        # The children list in the 'subdir' node is empty below,
        # because the root-dir-nodes API endpoint is designed to
        # only show files and folders immediately within the dataset's
        # top-level directory:
        expected_data = [
            {
                "name": "filename1",
                "id": df1.id,
                "verified": False,
                "is_online": True,
                "recall_url": None,
            },
            {"name": "subdir", "path": "subdir", "children": []},
            {"next_page": False},
        ]
        self.assertEqual(
            sorted(returned_data, key=lambda x: ("name" not in x, x.get("name", None))),
            sorted(expected_data, key=lambda x: ("name" not in x, x.get("name", None))),
        )

        dataset.delete()

    def test_get_child_dir_nodes(self):
        dataset = Dataset.objects.create(description="test dataset")
        dataset.experiments.add(self.testexp)
        dataset.save()
        uri = "/api/v1/dataset/%d/child-dir-nodes/?dir_path=subdir" % dataset.id
        response = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data, [])

        df1 = DataFile.objects.create(
            dataset=dataset,
            filename="filename1",
            size=0,
            md5sum="bogus",
            directory="subdir",
        )
        response = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(
            returned_data,
            [
                {
                    "name": "filename1",
                    "id": df1.id,
                    "verified": False,
                    "is_online": True,
                    "recall_url": None,
                }
            ],
        )

        df2 = DataFile.objects.create(
            dataset=dataset,
            filename="filename2",
            size=0,
            md5sum="bogus",
            directory="subdir",
        )
        response = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        expected_data = [
            {
                "name": "filename1",
                "id": df1.id,
                "verified": False,
                "is_online": True,
                "recall_url": None,
            },
            {
                "name": "filename2",
                "id": df2.id,
                "verified": False,
                "is_online": True,
                "recall_url": None,
            },
        ]
        self.assertEqual(
            sorted(returned_data, key=lambda x: x["name"]),
            sorted(expected_data, key=lambda x: x["name"]),
        )

        DataFile.objects.create(
            dataset=dataset,
            filename="filename3",
            size=0,
            md5sum="bogus",
            directory="subdir2",
        )
        response = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        # 'filename3' is not in the dir_path we are querying,
        # so it shouldn't appear in the results:
        expected_data = [
            {
                "name": "filename1",
                "id": df1.id,
                "verified": False,
                "is_online": True,
                "recall_url": None,
            },
            {
                "name": "filename2",
                "id": df2.id,
                "verified": False,
                "is_online": True,
                "recall_url": None,
            },
        ]
        self.assertEqual(
            sorted(returned_data, key=lambda x: x["name"]),
            sorted(expected_data, key=lambda x: x["name"]),
        )

        df4 = DataFile.objects.create(
            dataset=dataset,
            filename="filename4",
            size=0,
            md5sum="bogus",
            directory="subdir/subdir3",
        )
        response = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        expected_data = [
            {
                "name": "filename1",
                "id": df1.id,
                "verified": False,
                "is_online": True,
                "recall_url": None,
            },
            {
                "name": "filename2",
                "id": df2.id,
                "verified": False,
                "is_online": True,
                "recall_url": None,
            },
            {"name": "subdir3", "path": "subdir/subdir3", "children": []},
        ]
        self.assertEqual(
            sorted(returned_data, key=lambda x: x["name"]),
            sorted(expected_data, key=lambda x: x["name"]),
        )

        uri = "/api/v1/dataset/%d/child-dir-nodes/?dir_path=subdir/subdir3" % dataset.id
        response = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        expected_data = [
            {
                "name": "filename4",
                "id": df4.id,
                "verified": False,
                "is_online": True,
                "recall_url": None,
            },
        ]
        self.assertEqual(
            sorted(returned_data, key=lambda x: x["name"]),
            sorted(expected_data, key=lambda x: x["name"]),
        )

        dataset.delete()

    def test_get_child_dir_nodes_no_files_in_root_dir(self):
        dataset = Dataset.objects.create(description="test dataset")
        dataset.experiments.add(self.testexp)
        dataset.save()
        encoded_subdir1 = quote("subdir#1")
        uri = "/api/v1/dataset/%d/child-dir-nodes/?dir_path=%s" % (
            dataset.id,
            encoded_subdir1,
        )

        df1 = DataFile.objects.create(
            dataset=dataset,
            filename="filename1",
            size=0,
            md5sum="bogus",
            directory="subdir#1",
        )
        response = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(
            returned_data,
            [
                {
                    "name": "filename1",
                    "id": df1.id,
                    "verified": False,
                    "is_online": True,
                    "recall_url": None,
                }
            ],
        )

        DataFile.objects.create(
            dataset=dataset,
            filename="filename2",
            size=0,
            md5sum="bogus",
            directory="subdir#1/subdir#2",
        )
        uri = "/api/v1/dataset/%d/child-dir-nodes/?dir_path=%s" % (
            dataset.id,
            encoded_subdir1,
        )
        response = self.api_client.get(uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        expected_data = [
            {
                "name": "filename1",
                "id": df1.id,
                "verified": False,
                "is_online": True,
                "recall_url": None,
            },
            {"name": "subdir#2", "path": "subdir#1/subdir#2", "children": []},
        ]
        self.assertEqual(
            sorted(returned_data, key=lambda x: x["name"]),
            sorted(expected_data, key=lambda x: x["name"]),
        )


class DatasetResourceAuthTest(MyTardisResourceTestCase):
    """
    Test the DatasetResource APIs and counts for both the MacroACL (Exp only ACLs)
    and MicroACL (all level ACLs) scenarios
    """

    def setUp(self):
        super().setUp()
        # create two users: one that will have no ACLs and will only see public
        # objects, and another user that will have ACLs for a subset of objects
        self.user_noacls = User.objects.create_user(
            username="noacls", password="noaclspassword"
        )
        self.user_someacls = User.objects.create_user(
            username="someacls", password="someaclspassword"
        )

        self.testds = Dataset()
        self.testds.description = "test dataset"
        self.testds.save()
        self.testds.experiments.add(self.testexp)

    def get_acl_credentials(self, username, password):
        return self.create_basic(username=username, password=password)

    def test_get_dataset_counts_macro(self):
        set_id = self.testds.id
        expected_output = {
            "dataset_size": 0,
            "dataset_datafile_count": 0,
        }
        output = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id, authentication=self.get_credentials()
        )
        returned_data = json.loads(output.content.decode())
        # Values should all be zero as no datafiles created yet
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        self.df1 = DataFile(
            dataset=self.testds, filename="1.txt", size="42", md5sum="bogus"
        )
        self.df1.save()

        self.df2 = DataFile(
            dataset=self.testds, filename="2.txt", size="42", md5sum="bogus"
        )
        self.df2.save()

        expected_output = {
            "dataset_size": 84,
            "dataset_datafile_count": 2,
        }
        output = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id, authentication=self.get_credentials()
        )
        returned_data = json.loads(output.content.decode())
        # Values should all be non-zero now that datafiles exist
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # Try to access the dataset with the no_acl user - should fail as parent exp not public
        response = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_acl_credentials("noacls", "noaclspassword"),
        )
        self.assertEqual(response.status_code, 401)
        # Try to access the dataset with the some_acl user - should fail as no acls yet
        response = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_acl_credentials("someacls", "someaclspassword"),
        )
        self.assertEqual(response.status_code, 401)

        self.someacl_acl = ExperimentACL(
            experiment=self.testexp,
            user=self.user_someacls,
            canRead=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        self.someacl_acl.save()

        # try again for user_someacls - this time it should work
        response = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_acl_credentials("someacls", "someaclspassword"),
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())

        # user_someacls should now see the same output from above
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # update the experiment to be public, allowing user_noacls to see the set
        self.testexp.public_access = 100
        self.testexp.save()

        # try again for user_noacls - this time it should work
        response = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_acl_credentials("noacls", "noaclspassword"),
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())

        # user_noacls should now see the same output from above
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # revert the testexp public setting
        self.testexp.public_access = 1
        self.testexp.save()

    @override_settings(ONLY_EXPERIMENT_ACLS=False)
    def test_get_dataset_counts_micro(self):
        set_id = self.testds.id
        expected_output_blank = {
            "dataset_size": 0,
            "dataset_datafile_count": 0,
        }
        output = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id, authentication=self.get_credentials()
        )
        returned_data = json.loads(output.content.decode())
        # Values should all be zero as no datafiles created yet
        for key, value in expected_output_blank.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        self.df1 = DataFile(
            dataset=self.testds, filename="1.txt", size="42", md5sum="bogus"
        )
        self.df1.save()

        self.df2 = DataFile(
            dataset=self.testds, filename="2.txt", size="42", md5sum="bogus"
        )
        self.df2.save()

        output = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id, authentication=self.get_credentials()
        )
        returned_data = json.loads(output.content.decode())
        # Values should still be zero as no DatafileACLs created
        for key, value in expected_output_blank.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # create Dataset ACL for self.user
        self.ds_acl = DatasetACL(
            dataset=self.testds,
            user=self.user,
            canRead=True,
            aclOwnershipType=DatasetACL.OWNER_OWNED,
        )
        self.ds_acl.save()

        # create Datafile ACLs for self.user
        for df in [self.df1, self.df2]:
            df_acl = DatafileACL(
                datafile=df,
                user=self.user,
                canRead=True,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
            df_acl.save()

        expected_output_full = {
            "dataset_size": 84,
            "dataset_datafile_count": 2,
        }
        output = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id, authentication=self.get_credentials()
        )
        returned_data = json.loads(output.content.decode())
        # self.user should now see the full size and counts due to ACLs
        for key, value in expected_output_full.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # Try to access the dataset with the no_acl user - should fail as set not public
        response = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_acl_credentials("noacls", "noaclspassword"),
        )
        self.assertEqual(response.status_code, 401)
        # Try to access the dataset with the some_acl user - should fail as no acls yet
        response = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_acl_credentials("someacls", "someaclspassword"),
        )
        self.assertEqual(response.status_code, 401)

        self.someacl_acl = DatasetACL(
            dataset=self.testds,
            user=self.user_someacls,
            canRead=True,
            aclOwnershipType=DatasetACL.OWNER_OWNED,
        )
        self.someacl_acl.save()

        # try again for user_someacls - this time it should return 200
        response = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_acl_credentials("someacls", "someaclspassword"),
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())

        # user_someacls should not see any counts/sizes as they have no micro access
        for key, value in expected_output_blank.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # create Datafile ACL for user_someacls for df1
        self.usersome_df_acl = DatafileACL(
            datafile=self.df1,
            user=self.user_someacls,
            canRead=True,
            aclOwnershipType=DatafileACL.OWNER_OWNED,
        )
        self.usersome_df_acl.save()

        expected_output_half = {
            "dataset_size": 42,
            "dataset_datafile_count": 1,
        }
        output = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_acl_credentials("someacls", "someaclspassword"),
        )
        returned_data = json.loads(output.content.decode())
        # user_someacls should now see the 1 datafile, and size=42
        for key, value in expected_output_half.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # update the experiment to be public, allowing user_noacls to see the exp
        self.testexp.public_access = 100
        self.testexp.save()

        # try again for user_noacls - this still shouldn't work
        response = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_acl_credentials("noacls", "noaclspassword"),
        )
        self.assertEqual(response.status_code, 401)
        returned_data = json.loads(response.content.decode())

        # update the dataset to be public, allowing user_noacls to see the set
        self.testds.public_access = 100
        self.testds.save()

        # try again for user_noacls - this should now work
        response = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_acl_credentials("noacls", "noaclspassword"),
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())

        # user_noacls should now see the same blank output from above as df are not public
        for key, value in expected_output_blank.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # update the df1 to be public, allowing user_noacls to see the file
        self.df1.public_access = 100
        self.df1.save()

        output = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_acl_credentials("noacls", "noaclspassword"),
        )
        returned_data = json.loads(output.content.decode())
        # user_noacls should now see the 1 datafile in the count
        for key, value in expected_output_half.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # update the df2 to be public, allowing user_noacls to see it
        self.df2.public_access = 100
        self.df2.save()

        output = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_acl_credentials("noacls", "noaclspassword"),
        )
        returned_data = json.loads(output.content.decode())
        # user_noacls should now see 2 datafiles, and size=84
        for key, value in expected_output_full.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        output = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_acl_credentials("someacls", "someaclspassword"),
        )
        returned_data = json.loads(output.content.decode())
        # user_someacls should now see 2 datafiles, and size=84
        for key, value in expected_output_full.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        output = self.api_client.get(
            "/api/v1/dataset/%d/" % set_id,
            authentication=self.get_credentials(),
        )
        returned_data = json.loads(output.content.decode())
        # self.user should still see the full results, hopefully no double counting
        # due to public flags (counts check ACLs + public and combine using distinct)
        for key, value in expected_output_full.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)
