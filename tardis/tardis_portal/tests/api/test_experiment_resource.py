'''
Testing the Experiment resource in MyTardis's Tastypie-based REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import json

from django.contrib.auth.models import User

from ...models.experiment import Experiment, ExperimentAuthor
from ...models.parameters import (ExperimentParameter,
                                  ExperimentParameterSet,
                                  ParameterName,
                                  Schema)

from . import MyTardisResourceTestCase


class ExperimentResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super().setUp()
        df_schema_name = "http://experi-mental.com/"
        self.test_schema = Schema(namespace=df_schema_name,
                                  type=Schema.EXPERIMENT)
        self.test_schema.save()
        self.test_parname1 = ParameterName(schema=self.test_schema,
                                           name="expparameter1",
                                           data_type=ParameterName.STRING)
        self.test_parname1.save()
        self.test_parname2 = ParameterName(schema=self.test_schema,
                                           name="expparameter2",
                                           data_type=ParameterName.NUMERIC)
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
                            "string_value": "Test16"
                        },
                        {
                            "name": "/api/v1/parametername/%d/" % (parm_id + 1),
                            "numerical_value": "244"
                        }
                    ]
                },
                {
                    "schema": "/api/v1/schema/%d/" % schema_id,
                    "parameters": [
                        {
                            "name": "expparameter1",
                            "string_value": "Test16"
                        },
                        {
                            "name": "expparameter2",
                            "value": "51244"
                        }
                    ]
                }
            ],
            "title": "testing parset creation2"
        }
        experiment_count = Experiment.objects.count()
        parameterset_count = ExperimentParameterSet.objects.count()
        parameter_count = ExperimentParameter.objects.count()
        self.assertHttpCreated(self.api_client.post(
            '/api/v1/experiment/',
            data=post_data,
            authentication=self.get_credentials()))
        self.assertEqual(experiment_count + 1, Experiment.objects.count())
        self.assertEqual(parameterset_count + 2,
                         ExperimentParameterSet.objects.count())
        self.assertEqual(parameter_count + 4,
                         ExperimentParameter.objects.count())

        # Now try creating an ExperimentAuthor record:
        exp_id = Experiment.objects.first().id
        post_data = {
            "experiment": "/api/v1/experiment/%s/" % exp_id,
            "author": "Author Name",
            "order": 1
        }
        self.assertHttpCreated(self.api_client.post(
            '/api/v1/experimentauthor/',
            data=post_data,
            authentication=self.get_credentials()))

    def test_get_experiment(self):
        exp_id = Experiment.objects.first().id
        user_id = 2 #User.objects.first().id, PUBLIC_USER is created first
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
            "url": None
        }
        output = self.api_client.get('/api/v1/experiment/%d/' % exp_id,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
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
            order=1)
        expected_output = {
            "author": "Author Name",
            "email": "Author.Name@example.com",
            "order": 1,
            "url": None
        }
        output = self.api_client.get(
            '/api/v1/experimentauthor/%d/' % exp_author.id,
            authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        for key, value in expected_output.items():
            self.assertEqual(returned_data[key], value)
        self.assertEqual(
            returned_data["experiment"]["id"], exp.id)
        self.assertEqual(
            returned_data["experiment"]["resource_uri"],
            "/api/v1/experiment/%d/" % exp.id)
