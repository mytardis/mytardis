"""
Testing the DatasetParameter and DatasetParameterSet resources in
MyTardis's Tastypie-based REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""
from django.contrib.auth.models import Permission

from ...models.dataset import Dataset
from ...models.parameters import (
    Schema,
    ParameterName,
    DatasetParameter,
    DatasetParameterSet,
)

from . import MyTardisResourceTestCase


class DatasetParameterSetResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super().setUp()
        self.test_schema = Schema.objects.create(
            namespace="http://schema.namespace/dataset/1", type=Schema.DATASET
        )
        self.test_param1_name = ParameterName.objects.create(
            schema=self.test_schema, name="param1_name", data_type=ParameterName.STRING
        )
        self.test_dataset = Dataset.objects.create(description="Test dataset")
        # Add to experiment with ObjectACL granting access to self.user
        # so auth with self.get_credentials() will succeed:
        self.test_dataset.experiments.add(self.testexp)
        # Create an extra dataset with metadata to ensure user already has access to the
        # relevant Schema and ParameterName URIs when referring to them during post requests
        self.prior_ds = Dataset.objects.create(description="Prior dataset")
        self.prior_ds.experiments.add(self.testexp)
        self.prior_ds_ps = DatasetParameterSet(
            schema=self.test_schema, dataset=self.prior_ds
        )
        self.prior_ds_ps.save()
        self.prior_ds_param1 = DatasetParameter(
            parameterset=self.prior_ds_ps,
            name=self.test_param1_name,
            string_value="prior data",
        )
        self.prior_ds_param1.save()

    def tearDown(self):
        self.test_schema.delete()
        self.test_dataset.delete()
        self.prior_ds.delete()

    def test_post_dataset_with_params(self):
        """
        Test creating a dataset with metadata
        """
        schema_uri = "/api/v1/schema/%s/" % self.test_schema.id
        param1_name_uri = "/api/v1/parametername/%s/" % self.test_param1_name.id
        experiment_uri = "/api/v1/experiment/%s/" % self.testexp.id
        post_data = {
            "description": "api test dataset parameters",
            "experiments": [experiment_uri],
            "parameter_sets": [
                {
                    "schema": schema_uri,
                    "parameters": [
                        {"name": param1_name_uri, "value": "value for param1"}
                    ],
                }
            ],
            "immutable": False,
        }
        dataset_count = Dataset.objects.count()
        self.assertHttpCreated(
            self.api_client.post(
                "/api/v1/dataset/",
                data=post_data,
                authentication=self.get_credentials(),
            )
        )
        self.assertEqual(dataset_count + 1, Dataset.objects.count())
        new_dataset = Dataset.objects.order_by("-id").first()
        psets = DatasetParameterSet.objects.filter(dataset=new_dataset)
        self.assertEqual(psets.count(), 1)
        self.assertEqual(psets[0].schema.namespace, self.test_schema.namespace)
        params = DatasetParameter.objects.filter(parameterset=psets[0])
        self.assertEqual(params.count(), 1)
        self.assertEqual(params[0].string_value, "value for param1")

    def test_create_dataset_pset(self):
        """
        Test creating a dataset parameter set
        """
        test_dataset_uri = "/api/v1/dataset/%s/" % self.test_dataset.id
        schema_uri = "/api/v1/schema/%s/" % self.test_schema.id
        param1_name_uri = "/api/v1/parametername/%s/" % self.test_param1_name.id
        post_data = {
            "dataset": test_dataset_uri,
            "schema": schema_uri,
            "parameters": [{"name": param1_name_uri, "value": "value for param1"}],
        }
        self.assertHttpCreated(
            self.api_client.post(
                "/api/v1/datasetparameterset/",
                data=post_data,
                authentication=self.get_credentials(),
            )
        )

    def test_create_dataset_pset_no_auth(self):
        """
        Test attempting to create a dataset parameter set without access
        """
        self.user.user_permissions.remove(
            Permission.objects.get(codename="change_dataset")
        )
        test_dataset_uri = "/api/v1/dataset/%s/" % self.test_dataset.id
        schema_uri = "/api/v1/schema/%s/" % self.test_schema.id
        param1_name_uri = "/api/v1/parametername/%s/" % self.test_param1_name.id
        post_data = {
            "dataset": test_dataset_uri,
            "schema": schema_uri,
            "parameters": [{"name": param1_name_uri, "value": "value for param1"}],
        }
        self.assertHttpUnauthorized(
            self.api_client.post(
                "/api/v1/datasetparameterset/",
                data=post_data,
                authentication=self.get_credentials(),
            )
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename="change_dataset")
        )


class DatasetParameterResourceTest(MyTardisResourceTestCase):
    pass
