import json
import os
import unittest
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import modify_settings, override_settings

from tardis.tardis_portal.models import DataFile, Dataset
from tardis.tardis_portal.tests.api import MyTardisResourceTestCase


@override_settings(SINGLE_SEARCH_ENABLED=True,
                   ELASTICSEARCH_DSL={
                       'default': {
                           'hosts': os.environ.get('ELASTICSEARCH_URL', None)
                       },
                   }
                   )
@modify_settings(INSTALLED_APPS={
    'append': 'django_elasticsearch_dsl'
})
@unittest.skipUnless(
        os.environ.get('ELASTICSEARCH_URL', None),
        "--elasticsearch not set"
    )
class SimpleSearchTest(MyTardisResourceTestCase):
    def setUp(self):
        super().setUp()
        self.out = StringIO()
        call_command('search_index', stdout=self.out,
                     action='delete', force=True)
        call_command('search_index', stdout=self.out,
                     action='rebuild', force=True)
        # add dataset and datafile to experiment
        self.dataset1 = Dataset(description='test_dataset')
        self.dataset1.save()
        self.dataset1.experiments.add(self.testexp)
        self.dataset1.save()
        settings.REQUIRE_DATAFILE_SIZES = False
        settings.REQUIRE_DATAFILE_CHECKSUMS = False
        self.datafile = DataFile(dataset=self.dataset1, filename='test.txt')
        self.datafile.save()

    def test_simple_search_authenticated_user(self):
        response = self.api_client.get('/api/v1/search_simple-search/?query=test',
                                       authentication=self.get_credentials())
        data = json.loads(response.content.decode())
        self.assertEqual(len(data['objects'][0]['hits']['experiments']), 1)
        self.assertEqual(len(data['objects'][0]['hits']['datasets']), 1)
        self.assertEqual(len(data['objects'][0]['hits']['datafiles']), 1)

    def test_simple_search_unauthenticated_user(self):
        self.testexp.public_access = 100
        self.testexp.save()
        response = self.api_client.get('/api/v1/search_simple-search/?query=test')
        data = json.loads(response.content.decode())
        self.assertEqual(len(data['objects'][0]['hits']['experiments']), 1)
        self.assertEqual(len(data['objects'][0]['hits']['datasets']), 1)
        self.assertEqual(len(data['objects'][0]['hits']['datafiles']), 1)

    def test_advance_search_unauthenticated_user(self):
        self.testexp.public_access = 100
        self.testexp.save()
        response = self.api_client.post('/api/v1/search_advance-search/',
                                        data={"text": "test", "TypeTag": ["Dataset", "Experiment", "Datafile"]})
        data = json.loads(response.content.decode())
        self.assertEqual(len(data['hits']['experiments']), 1)
        self.assertEqual(len(data['hits']['datasets']), 1)
        self.assertEqual(len(data['hits']['datafiles']), 1)

    def test_advance_search_authenticated_user(self):
        response = self.api_client.post('/api/v1/search_advance-search/',
                                        data={"text": "test", "TypeTag": ["Dataset", "Experiment", "Datafile"]},
                                        authentication=self.get_credentials())
        data = json.loads(response.content.decode())
        self.assertEqual(len(data['hits']['experiments']), 1)
        self.assertEqual(len(data['hits']['datasets']), 1)
        self.assertEqual(len(data['hits']['datafiles']), 1)
