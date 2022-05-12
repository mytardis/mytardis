"""
Testing the following resources in MyTardis's Tastypie-based REST API to ensure
sensitive parameters are not exposed without correct permissions:
 - Experiment, ExperimentParameter, ExperimentParameterSet
 - Dataset, DatasetParameter, DatasetParameterSet
 - DataFile, DatafileParameter, DatafileParameterSet
 - ParameterName
 Tests for both object lists and details APIs

.. moduleauthor:: Mike Laverick <mike.laverick@auckland.ac.nz>
"""
import json
from unittest import skipIf

from django.conf import settings
from django.contrib.auth.models import User
from django.test.client import Client

from ...models.access_control import ExperimentACL, DatasetACL, DatafileACL
from ...models.experiment import Experiment
from ...models.dataset import Dataset
from ...models.datafile import DataFile

from ...models.parameters import (
    ExperimentParameter,
    ExperimentParameterSet,
    DatasetParameter,
    DatasetParameterSet,
    DatafileParameter,
    DatafileParameterSet,
    ParameterName,
    Schema,
)

from . import MyTardisResourceTestCase


class SensitiveMetadataTest(MyTardisResourceTestCase):
    def setUp(self):
        super().setUp()
        self.django_client = Client()
        self.django_client.login(username=self.username, password=self.password)

        self.user2 = User.objects.create_user("no_sensitive", "no@sens.com", "access")

        self.django_client_non_sens = Client()
        self.django_client_non_sens.login(username="no_sensitive", password="access")

        self.exp_sens = Experiment(
            title="test exp", institution_name="auckland", created_by=self.user
        )
        self.exp_sens.save()

        self.acl = ExperimentACL(
            user=self.user,
            experiment=self.exp_sens,
            canRead=True,
            canSensitive=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        self.acl.save()

        self.acl2 = ExperimentACL(
            user=self.user2,
            experiment=self.exp_sens,
            canRead=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        self.acl2.save()

        self.set_sens = Dataset()
        self.set_sens.description = "Dataset with sensitive parameters"
        self.set_sens.save()
        self.set_sens.experiments.add(self.exp_sens)

        self.file_sens = DataFile(
            dataset=self.set_sens, filename="testfile.txt", size="42", md5sum="bogus"
        )
        self.file_sens.save()

        sens_schema_name = "http://topsecret.com/"
        self.sens_schema = Schema(namespace=sens_schema_name, type=Schema.DATAFILE)
        self.sens_schema.save()
        self.parname = ParameterName(
            schema=self.sens_schema,
            name="normalparameter",
            data_type=ParameterName.STRING,
        )
        self.parname.save()
        self.sens_parname = ParameterName(
            schema=self.sens_schema,
            name="sensitiveparameter",
            data_type=ParameterName.STRING,
            sensitive=True,
        )
        self.sens_parname.save()

        self.exp_paramset = ExperimentParameterSet(
            schema=self.sens_schema, experiment=self.exp_sens
        )
        self.exp_paramset.save()
        self.exp_par = ExperimentParameter(
            parameterset=self.exp_paramset,
            name=self.parname,
            string_value="normal data",
        )
        self.exp_par.save()
        self.exp_par_sens = ExperimentParameter(
            parameterset=self.exp_paramset,
            name=self.sens_parname,
            string_value="sensitive",
        )
        self.exp_par_sens.save()

        self.set_paramset = DatasetParameterSet(
            schema=self.sens_schema, dataset=self.set_sens
        )
        self.set_paramset.save()
        self.set_par = DatasetParameter(
            parameterset=self.set_paramset,
            name=self.parname,
            string_value="normal data",
        )
        self.set_par.save()
        self.set_par_sens = DatasetParameter(
            parameterset=self.set_paramset,
            name=self.sens_parname,
            string_value="sensitive",
        )
        self.set_par_sens.save()

        self.file_paramset = DatafileParameterSet(
            schema=self.sens_schema, datafile=self.file_sens
        )
        self.file_paramset.save()
        self.file_par = DatafileParameter(
            parameterset=self.file_paramset,
            name=self.parname,
            string_value="normal data",
        )
        self.file_par.save()
        self.file_par_sens = DatafileParameter(
            parameterset=self.file_paramset,
            name=self.sens_parname,
            string_value="sensitive",
        )
        self.file_par_sens.save()

    def assert_obj_list(self, returned_data, value_list):
        self.assertEqual(
            sorted(
                [
                    x["string_value"]
                    for z in returned_data["objects"]
                    for y in z["parameter_sets"]
                    for x in y["parameters"]
                ],
            ),
            value_list,
        )

    def assert_obj_detail(self, returned_data, value_list):
        self.assertEqual(
            sorted(
                [
                    x["string_value"]
                    for y in returned_data["parameter_sets"]
                    for x in y["parameters"]
                ],
            ),
            value_list,
        )

    def assert_paramset_list(self, returned_data, value_list):
        self.assertEqual(
            sorted(
                [
                    x["string_value"]
                    for y in returned_data["objects"]
                    for x in y["parameters"]
                ],
            ),
            value_list,
        )

    def assert_paramset_detail(self, returned_data, value_list):
        self.assertEqual(
            sorted(
                [x["string_value"] for x in returned_data["parameters"]],
            ),
            value_list,
        )

    def assert_param_list(self, returned_data, value_list):
        self.assertEqual(
            sorted([x["id"] for x in returned_data["objects"]]), value_list
        )

    def create_acl(self, user, obj, sens_perm, obj_type):
        if obj_type == "exp":
            acl = ExperimentACL(
                user=user,
                experiment=obj,
                canRead=True,
                canSensitive=sens_perm,
                aclOwnershipType=ExperimentACL.OWNER_OWNED,
            )
        if obj_type == "set":
            acl = DatasetACL(
                user=user,
                dataset=obj,
                canRead=True,
                canSensitive=sens_perm,
                aclOwnershipType=DatasetACL.OWNER_OWNED,
            )
        if obj_type == "file":
            acl = DatafileACL(
                user=user,
                datafile=obj,
                canRead=True,
                canSensitive=sens_perm,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
        acl.save()

    def test_experiment_list_api(self):
        response = self.django_client.get("/api/v1/experiment/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_list(returned_data, ["normal data", "sensitive"])

        response = self.django_client_non_sens.get("/api/v1/experiment/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_list(returned_data, ["normal data"])

    def test_experiment_detail_api(self):
        response = self.django_client.get("/api/v1/experiment/%s/" % self.exp_sens.id)
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_detail(returned_data, ["normal data", "sensitive"])

        response = self.django_client_non_sens.get(
            "/api/v1/experiment/%s/" % self.exp_sens.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_detail(returned_data, ["normal data"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == False, "skipping Macro ACL specific test")
    def test_dataset_list_api_macro(self):
        response = self.django_client.get("/api/v1/dataset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_list(returned_data, ["normal data", "sensitive"])

        response = self.django_client_non_sens.get("/api/v1/dataset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_list(returned_data, ["normal data"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == True, "skipping Micro ACL specific test")
    def test_dataset_list_api_micro(self):
        # User2 shouldnt be able to see the sensitive metadata without a sens datasetACL
        self.create_acl(self.user2, self.exp_sens, True, "exp")
        self.create_acl(self.user2, self.set_sens, False, "set")
        response = self.django_client_non_sens.get("/api/v1/dataset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_list(returned_data, ["normal data"])

        self.create_acl(self.user2, self.set_sens, True, "set")
        # User2 should now be able to see the sensitive metadata
        response = self.django_client_non_sens.get("/api/v1/dataset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_list(returned_data, ["normal data", "sensitive"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == False, "skipping Macro ACL specific test")
    def test_dataset_detail_api_macro(self):
        response = self.django_client.get("/api/v1/dataset/%s/" % self.set_sens.id)
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_detail(returned_data, ["normal data", "sensitive"])

        response = self.django_client_non_sens.get(
            "/api/v1/dataset/%s/" % self.set_sens.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_detail(returned_data, ["normal data"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == True, "skipping Micro ACL specific test")
    def test_dataset_detail_api_micro(self):
        # User2 shouldnt be able to see the sensitive metadata without a sens datasetACL
        self.create_acl(self.user2, self.exp_sens, True, "exp")
        self.create_acl(self.user2, self.set_sens, False, "set")
        response = self.django_client_non_sens.get(
            "/api/v1/dataset/%s/" % self.set_sens.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_detail(returned_data, ["normal data"])

        self.create_acl(self.user2, self.set_sens, True, "set")
        # User2 should now be able to see the sensitive metadata
        response = self.django_client_non_sens.get(
            "/api/v1/dataset/%s/" % self.set_sens.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_detail(returned_data, ["normal data", "sensitive"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == False, "skipping Macro ACL specific test")
    def test_datafile_list_api_macro(self):
        response = self.django_client.get("/api/v1/dataset_file/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_list(returned_data, ["normal data", "sensitive"])

        response = self.django_client_non_sens.get("/api/v1/dataset_file/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_list(returned_data, ["normal data"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == True, "skipping Micro ACL specific test")
    def test_datafile_list_api_micro(self):
        # User2 shouldnt be able to see the sensitive metadata without a sens datafileACL
        self.create_acl(self.user2, self.exp_sens, True, "exp")
        self.create_acl(self.user2, self.set_sens, True, "set")
        self.create_acl(self.user2, self.file_sens, False, "file")
        response = self.django_client_non_sens.get("/api/v1/dataset_file/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_list(returned_data, ["normal data"])

        self.create_acl(self.user2, self.file_sens, True, "file")
        # User2 should now be able to see the sensitive metadata
        response = self.django_client_non_sens.get("/api/v1/dataset_file/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_list(returned_data, ["normal data", "sensitive"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == False, "skipping Macro ACL specific test")
    def test_datafile_detail_api_macro(self):
        response = self.django_client.get(
            "/api/v1/dataset_file/%s/" % self.file_sens.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_detail(returned_data, ["normal data", "sensitive"])

        response = self.django_client_non_sens.get(
            "/api/v1/dataset_file/%s/" % self.file_sens.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_detail(returned_data, ["normal data"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == True, "skipping Micro ACL specific test")
    def test_datafile_detail_api_micro(self):
        # User2 shouldnt be able to see the sensitive metadata without a sens datasetACL
        self.create_acl(self.user2, self.exp_sens, True, "exp")
        self.create_acl(self.user2, self.set_sens, True, "set")
        self.create_acl(self.user2, self.file_sens, False, "file")
        response = self.django_client_non_sens.get(
            "/api/v1/dataset_file/%s/" % self.set_sens.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_detail(returned_data, ["normal data"])

        self.create_acl(self.user2, self.file_sens, True, "file")
        # User2 should now be able to see the sensitive metadata
        response = self.django_client_non_sens.get(
            "/api/v1/dataset_file/%s/" % self.set_sens.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_obj_detail(returned_data, ["normal data", "sensitive"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == False, "skipping Macro ACL specific test")
    def test_experimentparameter_list_api(self):
        response = self.django_client.get("/api/v1/experimentparameter/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_param_list(returned_data, [self.exp_par.id, self.exp_par_sens.id])

        response = self.django_client_non_sens.get("/api/v1/experimentparameter/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_param_list(returned_data, [self.exp_par.id])

    def test_experimentparameter_detail_api(self):
        response = self.django_client.get(
            "/api/v1/experimentparameter/%s/" % self.exp_par.id
        )
        self.assertEqual(response.status_code, 200)
        response = self.django_client.get(
            "/api/v1/experimentparameter/%s/" % self.exp_par_sens.id
        )
        self.assertEqual(response.status_code, 200)
        response = self.django_client_non_sens.get(
            "/api/v1/experimentparameter/%s/" % self.exp_par.id
        )
        self.assertEqual(response.status_code, 200)
        response = self.django_client_non_sens.get(
            "/api/v1/experimentparameter/%s/" % self.exp_par_sens.id
        )
        self.assertEqual(response.status_code, 401)

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == False, "skipping Macro ACL specific test")
    def test_datasetparameter_list_api_macro(self):
        response = self.django_client.get("/api/v1/datasetparameter/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_param_list(returned_data, [self.set_par.id, self.set_par_sens.id])

        response = self.django_client_non_sens.get("/api/v1/datasetparameter/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_param_list(returned_data, [self.set_par.id])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == True, "skipping Micro ACL specific test")
    def test_datasetparameter_list_api_micro(self):
        # User2 shouldnt be able to see the sensitive metadata without a sens datasetACL
        self.create_acl(self.user2, self.exp_sens, True, "exp")
        self.create_acl(self.user2, self.set_sens, False, "set")
        response = self.django_client_non_sens.get("/api/v1/datasetparameter/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_param_list(returned_data, [self.set_par.id])
        self.create_acl(self.user2, self.set_sens, True, "set")
        # User2 should now be able to see the sensitive metadata
        response = self.django_client_non_sens.get("/api/v1/datasetparameter/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_param_list(returned_data, [self.set_par.id, self.set_par_sens.id])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == False, "skipping Macro ACL specific test")
    def test_datasetparameter_detail_api_macro(self):
        response = self.django_client.get(
            "/api/v1/datasetparameter/%s/" % self.set_par.id
        )
        self.assertEqual(response.status_code, 200)
        response = self.django_client.get(
            "/api/v1/datasetparameter/%s/" % self.set_par_sens.id
        )
        self.assertEqual(response.status_code, 200)
        response = self.django_client_non_sens.get(
            "/api/v1/datasetparameter/%s/" % self.set_par.id
        )
        self.assertEqual(response.status_code, 200)
        response = self.django_client_non_sens.get(
            "/api/v1/datasetparameter/%s/" % self.set_par_sens.id
        )
        self.assertEqual(response.status_code, 401)

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == True, "skipping Micro ACL specific test")
    def test_datasetparameter_detail_api_micro(self):
        # User2 shouldnt be able to see the sensitive metadata without a sens datasetACL
        self.create_acl(self.user2, self.exp_sens, True, "exp")
        self.create_acl(self.user2, self.set_sens, False, "set")
        response = self.django_client_non_sens.get(
            "/api/v1/datasetparameter/%s/" % self.set_par.id
        )
        self.assertEqual(response.status_code, 200)
        response = self.django_client_non_sens.get(
            "/api/v1/datasetparameter/%s/" % self.set_par_sens.id
        )
        self.assertEqual(response.status_code, 401)
        self.create_acl(self.user2, self.set_sens, True, "set")
        # User2 should now be able to see the sensitive metadata
        response = self.django_client_non_sens.get(
            "/api/v1/datasetparameter/%s/" % self.set_par_sens.id
        )
        self.assertEqual(response.status_code, 200)

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == False, "skipping Macro ACL specific test")
    def test_datafileparameter_list_api_macro(self):
        response = self.django_client.get("/api/v1/datafileparameter/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_param_list(returned_data, [self.file_par.id, self.file_par_sens.id])

        response = self.django_client_non_sens.get("/api/v1/datafileparameter/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_param_list(returned_data, [self.file_par.id])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == True, "skipping Micro ACL specific test")
    def test_datafileparameter_list_api_micro(self):
        # User2 shouldnt be able to see the sensitive metadata without a sens datafileACL
        self.create_acl(self.user2, self.exp_sens, True, "exp")
        self.create_acl(self.user2, self.set_sens, True, "set")
        self.create_acl(self.user2, self.file_sens, False, "file")
        response = self.django_client_non_sens.get("/api/v1/datafileparameter/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_param_list(returned_data, [self.file_par.id])
        self.create_acl(self.user2, self.file_sens, True, "file")
        # User2 should now be able to see the sensitive metadata
        response = self.django_client_non_sens.get("/api/v1/datafileparameter/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_param_list(returned_data, [self.file_par.id, self.file_par_sens.id])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == False, "skipping Macro ACL specific test")
    def test_datafileparameter_detail_api_macro(self):
        response = self.django_client.get(
            "/api/v1/datafileparameter/%s/" % self.file_par.id
        )
        self.assertEqual(response.status_code, 200)
        response = self.django_client.get(
            "/api/v1/datafileparameter/%s/" % self.file_par_sens.id
        )
        self.assertEqual(response.status_code, 200)
        response = self.django_client_non_sens.get(
            "/api/v1/datafileparameter/%s/" % self.file_par.id
        )
        self.assertEqual(response.status_code, 200)
        response = self.django_client_non_sens.get(
            "/api/v1/datafileparameter/%s/" % self.file_par_sens.id
        )
        self.assertEqual(response.status_code, 401)

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == True, "skipping Micro ACL specific test")
    def test_datafileparameter_detail_api_micro(self):
        # User2 shouldnt be able to see the sensitive metadata without a sens datafileACL
        self.create_acl(self.user2, self.exp_sens, True, "exp")
        self.create_acl(self.user2, self.set_sens, True, "set")
        self.create_acl(self.user2, self.file_sens, False, "file")
        response = self.django_client_non_sens.get(
            "/api/v1/datafileparameter/%s/" % self.file_par.id
        )
        self.assertEqual(response.status_code, 200)
        response = self.django_client_non_sens.get(
            "/api/v1/datafileparameter/%s/" % self.file_par_sens.id
        )
        self.assertEqual(response.status_code, 401)
        self.create_acl(self.user2, self.file_sens, True, "file")
        # User2 should now be able to see the sensitive metadata
        response = self.django_client_non_sens.get(
            "/api/v1/datafileparameter/%s/" % self.file_par_sens.id
        )
        self.assertEqual(response.status_code, 200)

    def test_experimentparameterset_list_api(self):
        response = self.django_client.get("/api/v1/experimentparameterset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_list(returned_data, ["normal data", "sensitive"])

        response = self.django_client_non_sens.get("/api/v1/experimentparameterset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_list(returned_data, ["normal data"])

    def test_experimentparameterset_detail_api(self):
        response = self.django_client.get(
            "/api/v1/experimentparameterset/%s/" % self.exp_paramset.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_detail(returned_data, ["normal data", "sensitive"])

        response = self.django_client_non_sens.get(
            "/api/v1/experimentparameterset/%s/" % self.exp_paramset.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_detail(returned_data, ["normal data"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == False, "skipping Macro ACL specific test")
    def test_datasetparameterset_list_api_macro(self):
        response = self.django_client.get("/api/v1/datasetparameterset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_list(returned_data, ["normal data", "sensitive"])

        response = self.django_client_non_sens.get("/api/v1/datasetparameterset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_list(returned_data, ["normal data"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == True, "skipping Micro ACL specific test")
    def test_datasetparameterset_list_api_micro(self):
        # User2 shouldnt be able to see the sensitive metadata without a sens datasetACL
        self.create_acl(self.user2, self.exp_sens, True, "exp")
        self.create_acl(self.user2, self.set_sens, False, "set")
        response = self.django_client_non_sens.get("/api/v1/datasetparameterset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_list(returned_data, ["normal data"])

        self.create_acl(self.user2, self.set_sens, True, "set")
        # User2 should now be able to see the sensitive metadata
        response = self.django_client_non_sens.get("/api/v1/datasetparameterset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_list(returned_data, ["normal data", "sensitive"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == False, "skipping Macro ACL specific test")
    def test_datasetparameterset_detail_api_macro(self):
        response = self.django_client.get(
            "/api/v1/datasetparameterset/%s/" % self.set_paramset.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_detail(returned_data, ["normal data", "sensitive"])

        response = self.django_client_non_sens.get(
            "/api/v1/datasetparameterset/%s/" % self.set_paramset.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_detail(returned_data, ["normal data"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == True, "skipping Micro ACL specific test")
    def test_datasetparameterset_detail_api_micro(self):
        # User2 shouldnt be able to see the sensitive metadata without a sens datasetACL
        self.create_acl(self.user2, self.exp_sens, True, "exp")
        self.create_acl(self.user2, self.set_sens, False, "set")
        response = self.django_client_non_sens.get(
            "/api/v1/datasetparameterset/%s/" % self.set_paramset.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_detail(returned_data, ["normal data"])

        self.create_acl(self.user2, self.set_sens, True, "set")
        # User2 should now be able to see the sensitive metadata
        response = self.django_client_non_sens.get(
            "/api/v1/datasetparameterset/%s/" % self.set_paramset.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_detail(returned_data, ["normal data", "sensitive"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == False, "skipping Macro ACL specific test")
    def test_datafileparameterset_list_api_macro(self):
        response = self.django_client.get("/api/v1/datafileparameterset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_list(returned_data, ["normal data", "sensitive"])

        response = self.django_client_non_sens.get("/api/v1/datafileparameterset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_list(returned_data, ["normal data"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == True, "skipping Micro ACL specific test")
    def test_datafileparameterset_list_api_micro(self):
        # User2 shouldnt be able to see the sensitive metadata without a sens datafileACL
        self.create_acl(self.user2, self.exp_sens, True, "exp")
        self.create_acl(self.user2, self.set_sens, True, "set")
        self.create_acl(self.user2, self.file_sens, False, "file")
        response = self.django_client_non_sens.get("/api/v1/datafileparameterset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_list(returned_data, ["normal data"])

        self.create_acl(self.user2, self.file_sens, True, "file")
        # User2 should now be able to see the sensitive metadata
        response = self.django_client_non_sens.get("/api/v1/datafileparameterset/")
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_list(returned_data, ["normal data", "sensitive"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == False, "skipping Macro ACL specific test")
    def test_datafileparameterset_detail_api_macro(self):
        response = self.django_client.get(
            "/api/v1/datafileparameterset/%s/" % self.file_paramset.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_detail(returned_data, ["normal data", "sensitive"])

        response = self.django_client_non_sens.get(
            "/api/v1/datafileparameterset/%s/" % self.file_paramset.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_detail(returned_data, ["normal data"])

    @skipIf(settings.ONLY_EXPERIMENT_ACLS == True, "skipping Micro ACL specific test")
    def test_datafileparameterset_detail_api_micro(self):
        # User2 shouldnt be able to see the sensitive metadata without a sens datafileACL
        self.create_acl(self.user2, self.exp_sens, True, "exp")
        self.create_acl(self.user2, self.set_sens, True, "set")
        self.create_acl(self.user2, self.file_sens, False, "file")
        response = self.django_client_non_sens.get(
            "/api/v1/datafileparameterset/%s/" % self.file_paramset.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_detail(returned_data, ["normal data"])

        self.create_acl(self.user2, self.file_sens, True, "file")
        # User2 should now be able to see the sensitive metadata
        response = self.django_client_non_sens.get(
            "/api/v1/datafileparameterset/%s/" % self.file_paramset.id
        )
        self.assertEqual(response.status_code, 200)
        returned_data = json.loads(response.content.decode())
        self.assert_paramset_detail(returned_data, ["normal data", "sensitive"])

    def test_parametername_list_api(self):
        # While "sensitive parameternames" are visible, sensitive parameter values
        # are not
        pass

    def test_parametername_detail_api(self):
        # While "sensitive parameternames" are visible, sensitive parameter values
        # are not
        pass

    def tearDown(self):
        self.exp_sens.delete()
        self.set_sens.delete()
        self.file_sens.delete()
        self.exp_paramset.delete()
        self.set_paramset.delete()
        self.file_paramset.delete()
        self.sens_schema.delete()
        self.user2.delete()
