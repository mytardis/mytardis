"""
Testing the Experiment resource in MyTardis's Tastypie-based REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
.. moduleauthor:: Mike Laverick <mike.laverick@auckland.ac.nz>
"""
import json
from pprint import pprint
from unittest import skipIf

from django.conf import settings
from django.contrib.auth.models import User

from ...models.access_control import DatafileACL, DatasetACL, ExperimentACL
from ...models.datafile import DataFile
from ...models.dataset import Dataset
from ...models.experiment import Experiment, ExperimentAuthor
from ...models.parameters import (
    ExperimentParameter,
    ExperimentParameterSet,
    ParameterName,
    Schema,
)
from . import MyTardisResourceTestCase


class ExperimentResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super().setUp()
        df_schema_name = "http://experi-mental.com/"
        self.test_schema = Schema(namespace=df_schema_name, type=Schema.EXPERIMENT)
        self.test_schema.save()
        self.test_parname1 = ParameterName(
            schema=self.test_schema,
            name="expparameter1",
            data_type=ParameterName.STRING,
        )
        self.test_parname1.save()
        self.test_parname2 = ParameterName(
            schema=self.test_schema,
            name="expparameter2",
            data_type=ParameterName.NUMERIC,
        )
        self.test_parname2.save()

    def test_post_experiment(self):
        schema_id = Schema.objects.first().id
        parm_id = ParameterName.objects.first().id
        post_data = {
            "description": "test description",
            "institution_name": "Monash University",
            "parameter_sets": [
                {
                    "schema": "http://experi-mental.com/",
                    "parameters": [
                        {
                            "name": "/api/v1/parametername/%d/" % parm_id,
                            "string_value": "Test16",
                        },
                        {
                            "name": "/api/v1/parametername/%d/" % (parm_id + 1),
                            "numerical_value": "244",
                        },
                    ],
                },
                {
                    "schema": "/api/v1/schema/%d/" % schema_id,
                    "parameters": [
                        {"name": "expparameter1", "string_value": "Test16"},
                        {"name": "expparameter2", "value": "51244"},
                    ],
                },
            ],
            "title": "testing parset creation2",
        }
        experiment_count = Experiment.objects.count()
        parameterset_count = ExperimentParameterSet.objects.count()
        parameter_count = ExperimentParameter.objects.count()
        pprint("Posting")
        response = self.api_client.post(
            "/api/v1/experiment/",
            data=post_data,
            authentication=self.get_credentials(),
        )
        pprint(response)
        pprint(response.request)
        pprint(response.json())
        pprint("End post")
        self.assertHttpCreated(
            self.api_client.post(
                "/api/v1/experiment/",
                data=post_data,
                authentication=self.get_credentials(),
            )
        )
        self.assertEqual(experiment_count + 1, Experiment.objects.count())
        self.assertEqual(parameterset_count + 2, ExperimentParameterSet.objects.count())
        self.assertEqual(parameter_count + 4, ExperimentParameter.objects.count())

        # Now try creating an ExperimentAuthor record:
        exp_id = Experiment.objects.first().id
        post_data = {
            "experiment": "/api/v1/experiment/%s/" % exp_id,
            "author": "Author Name",
            "order": 1,
        }
        self.assertHttpCreated(
            self.api_client.post(
                "/api/v1/experimentauthor/",
                data=post_data,
                authentication=self.get_credentials(),
            )
        )

    def test_get_experiment(self):
        exp_id = Experiment.objects.first().id
        user_id = 3  # PUBLIC_USER and PUBLIC_USER_TEST both exist first
        expected_output = {
            "approved": True,
            "created_by": "/api/v1/user/%d/" % user_id,
            "created_time": "2013-05-29T13:00:26.626580",
            "description": "",
            "end_time": None,
            "handle": None,
            "id": exp_id,
            "institution_name": "Monash University",
            "locked": False,
            "parameter_sets": [],
            "public_access": 1,
            "resource_uri": "/api/v1/experiment/%d/" % exp_id,
            "start_time": None,
            "title": "test exp",
            "update_time": "2013-05-29T13:00:26.626609",
            "url": None,
        }
        output = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id, authentication=self.get_credentials()
        )
        returned_data = json.loads(output.content.decode())
        print(returned_data)
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            if not key.endswith("_time"):
                self.assertEqual(returned_data[key], value)

    def test_get_experiment_author(self):
        exp = Experiment.objects.first()
        exp_author = ExperimentAuthor.objects.create(
            experiment=exp,
            author="Author Name",
            email="Author.Name@example.com",
            order=1,
        )
        expected_output = {
            "author": "Author Name",
            "email": "Author.Name@example.com",
            "order": 1,
            "url": None,
        }
        output = self.api_client.get(
            "/api/v1/experimentauthor/%d/" % exp_author.id,
            authentication=self.get_credentials(),
        )
        returned_data = json.loads(output.content.decode())
        for key, value in expected_output.items():
            self.assertEqual(returned_data[key], value)
        self.assertEqual(returned_data["experiment"]["id"], exp.id)
        self.assertEqual(
            returned_data["experiment"]["resource_uri"],
            "/api/v1/experiment/%d/" % exp.id,
        )


class ExperimentResourceCountsTest(MyTardisResourceTestCase):
    """
    Test the ExperimentResource counts for both the MacroACL (Exp only ACLs)
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

    def get_acl_credentials(self, username, password):
        return self.create_basic(username=username, password=password)

    @skipIf(settings.ONLY_EXPERIMENT_ACLS is False, "skipping Macro ACL specific test")
    def test_get_experiment_counts_macro(self):
        exp_id = Experiment.objects.first().id
        expected_output = {
            "dataset_count": 0,
            "experiment_size": 0,
            "datafile_count": 0,
        }
        output = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id, authentication=self.get_credentials()
        )
        returned_data = json.loads(output.content.decode())
        # Values should all be zero as no datasets or datafiles created yet
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        self.testds1 = Dataset()
        self.testds1.description = "test dataset"
        self.testds1.save()
        self.testds1.experiments.add(self.testexp)

        self.df1 = DataFile(
            dataset=self.testds1, filename="1.txt", size="42", md5sum="bogus"
        )
        self.df1.save()

        self.df2 = DataFile(
            dataset=self.testds1, filename="2.txt", size="42", md5sum="bogus"
        )
        self.df2.save()

        self.testds2 = Dataset()
        self.testds2.description = "test dataset 2"
        self.testds2.save()
        self.testds2.experiments.add(self.testexp)

        self.df3 = DataFile(
            dataset=self.testds2, filename="3.txt", size="42", md5sum="bogus"
        )
        self.df3.save()

        self.df4 = DataFile(
            dataset=self.testds2, filename="4.txt", size="42", md5sum="bogus"
        )
        self.df4.save()

        expected_output = {
            "dataset_count": 2,
            "experiment_size": 168,
            "datafile_count": 4,
        }
        output = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id, authentication=self.get_credentials()
        )
        returned_data = json.loads(output.content.decode())
        # Values should all be non-zero now that datasets and datafiles exist
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # Try to access the experiment with the no_acl user - should fail as exp not public
        response = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
            authentication=self.get_acl_credentials("noacls", "noaclspassword"),
        )
        self.assertEqual(response.status_code, 401)
        # Try to access the experiment with the some_acl user - should fail as no acls yet
        response = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
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
            "/api/v1/experiment/%d/" % exp_id,
            authentication=self.get_acl_credentials("someacls", "someaclspassword"),
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())

        # user_someacls should now see the same output from above
        for key, value in expected_output.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # update the experiment to be public, allowing user_noacls to see the exp
        self.testexp.public_access = 100
        self.testexp.save()

        # try again for user_noacls - this time it should work
        response = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
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

    @skipIf(settings.ONLY_EXPERIMENT_ACLS is True, "skipping Micro ACL specific test")
    def test_get_experiment_counts_micro(self):
        exp_id = Experiment.objects.first().id
        expected_output_blank = {
            "dataset_count": 0,
            "experiment_size": 0,
            "datafile_count": 0,
        }
        output = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id, authentication=self.get_credentials()
        )
        returned_data = json.loads(output.content.decode())
        # Values should all be zero as no datasets or datafiles created yet
        for key, value in expected_output_blank.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        self.testds1 = Dataset()
        self.testds1.description = "test dataset"
        self.testds1.save()
        self.testds1.experiments.add(self.testexp)

        self.df1 = DataFile(
            dataset=self.testds1, filename="1.txt", size="42", md5sum="bogus"
        )
        self.df1.save()

        self.df2 = DataFile(
            dataset=self.testds1, filename="2.txt", size="42", md5sum="bogus"
        )
        self.df2.save()

        self.testds2 = Dataset()
        self.testds2.description = "test dataset 2"
        self.testds2.save()
        self.testds2.experiments.add(self.testexp)

        self.df3 = DataFile(
            dataset=self.testds2, filename="3.txt", size="42", md5sum="bogus"
        )
        self.df3.save()

        self.df4 = DataFile(
            dataset=self.testds2, filename="4.txt", size="42", md5sum="bogus"
        )
        self.df4.save()

        output = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id, authentication=self.get_credentials()
        )
        returned_data = json.loads(output.content.decode())
        # Values should still be zero as no DatasetACLs or DatafileACLs created
        for key, value in expected_output_blank.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # create Dataset ACLs for self.user
        for ds in [self.testds1, self.testds2]:
            ds_acl = DatasetACL(
                dataset=ds,
                user=self.user,
                canRead=True,
                aclOwnershipType=DatasetACL.OWNER_OWNED,
            )
            ds_acl.save()

        # create Datafile ACLs for self.user
        for df in [self.df1, self.df2, self.df3, self.df4]:
            df_acl = DatafileACL(
                datafile=df,
                user=self.user,
                canRead=True,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
            df_acl.save()

        expected_output_full = {
            "dataset_count": 2,
            "experiment_size": 168,
            "datafile_count": 4,
        }
        output = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id, authentication=self.get_credentials()
        )
        returned_data = json.loads(output.content.decode())
        # self.user should now see the full size and counts due to ACLs
        for key, value in expected_output_full.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # Try to access the experiment with the no_acl user - should fail as exp not public
        response = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
            authentication=self.get_acl_credentials("noacls", "noaclspassword"),
        )
        self.assertEqual(response.status_code, 401)
        # Try to access the experiment with the some_acl user - should fail as no acls yet
        response = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
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

        # try again for user_someacls - this time it should return 200
        response = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
            authentication=self.get_acl_credentials("someacls", "someaclspassword"),
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())

        # user_someacls should not see any counts/sizes as they have no micro access
        for key, value in expected_output_blank.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # create ACL for user_someacls for dataset 1
        self.someacl_acl_ds = DatasetACL(
            dataset=self.testds1,
            user=self.user_someacls,
            canRead=True,
            aclOwnershipType=DatasetACL.OWNER_OWNED,
        )
        self.someacl_acl_ds.save()

        expected_output_ds = {
            "dataset_count": 1,
            "experiment_size": 0,
            "datafile_count": 0,
        }
        output = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
            authentication=self.get_acl_credentials("someacls", "someaclspassword"),
        )
        returned_data = json.loads(output.content.decode())
        # user_someacls should now see the 1 dataset in the count
        for key, value in expected_output_ds.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # create Datafile ACLs for user_someacls for df1 and df2 in testds1
        for df in [self.df1, self.df2]:
            df_acl = DatafileACL(
                datafile=df,
                user=self.user_someacls,
                canRead=True,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
            df_acl.save()

        expected_output_half = {
            "dataset_count": 1,
            "experiment_size": 84,
            "datafile_count": 2,
        }
        output = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
            authentication=self.get_acl_credentials("someacls", "someaclspassword"),
        )
        returned_data = json.loads(output.content.decode())
        # user_someacls should now see the 1 dataset, 2 datafiles, and size=84
        for key, value in expected_output_half.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # update the experiment to be public, allowing user_noacls to see the exp
        self.testexp.public_access = 100
        self.testexp.save()

        # try again for user_noacls - this time it should work
        response = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
            authentication=self.get_acl_credentials("noacls", "noaclspassword"),
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())

        # user_noacls should now see the same blank output from above as ds/df are not public
        for key, value in expected_output_blank.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # update the ds1 to be public, allowing user_noacls to see the set
        self.testds2.public_access = 100
        self.testds2.save()

        output = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
            authentication=self.get_acl_credentials("noacls", "noaclspassword"),
        )
        returned_data = json.loads(output.content.decode())
        # user_noacls should now see the 1 dataset in the count
        for key, value in expected_output_ds.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        expected_output_ds2 = {
            "dataset_count": 2,
            "experiment_size": 84,
            "datafile_count": 2,
        }

        output = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
            authentication=self.get_acl_credentials("someacls", "someaclspassword"),
        )
        returned_data = json.loads(output.content.decode())
        # user_someacls should now see 2 datasets, 2 datafiles, and size=84
        for key, value in expected_output_ds2.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        # update the df3 and 4 to be public, allowing user_noacls to see them
        self.df3.public_access = 100
        self.df3.save()
        self.df4.public_access = 100
        self.df4.save()

        output = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
            authentication=self.get_acl_credentials("noacls", "noaclspassword"),
        )
        returned_data = json.loads(output.content.decode())
        # user_noacls should now see 1 dataset, 2 datafiles, and size=84
        for key, value in expected_output_half.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        output = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
            authentication=self.get_acl_credentials("someacls", "someaclspassword"),
        )
        returned_data = json.loads(output.content.decode())
        # user_someacls should now see 2 datasets, 4 datafiles, and size=168
        for key, value in expected_output_full.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

        output = self.api_client.get(
            "/api/v1/experiment/%d/" % exp_id,
            authentication=self.get_credentials(),
        )
        returned_data = json.loads(output.content.decode())
        # self.user should still see the full results, hopefully no double counting
        # due to public flags (counts check ACLs + public and combine using distinct)
        for key, value in expected_output_full.items():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)
