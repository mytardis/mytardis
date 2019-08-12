import os
import json
import unittest

from django.test import modify_settings, override_settings
from django.core.management import call_command
from django.conf import settings
from django.utils.six import StringIO

from tardis.tardis_portal.models import Experiment, Dataset, DataFile
from tardis.tardis_portal.tests.api import MyTardisResourceTestCase


@override_settings(SINGLE_SEARCH_ENABLED=True)
@modify_settings(INSTALLED_APPS={
    'append': 'django_elasticsearch_dsl'
})
@override_settings(ELASTICSEARCH_DSL={
        'default': {
            'hosts': os.environ.get('ELASTICSEARCH_URL', None)
        },
})
@unittest.skipUnless(
        os.environ.get('ELASTICSEARCH_URL', None),
        "--elasticsearch not set"
    )
class SimpleSearchTest(MyTardisResourceTestCase):
    def setUp(self):
        super(SimpleSearchTest, self).setUp()
        self.out = StringIO()
        call_command('search_index', stdout=self.out,
                     action='delete', force=True)
        call_command('search_index', stdout=self.out,
                     action='rebuild', force=True)

    def test_simple_search(self):

        # add dataset and datafile to experiment
        self.dataset1 = Dataset(description='test_dataset')
        self.dataset1.save()
        self.dataset1.experiments.add(self.testexp)
        self.dataset1.save()

        settings.REQUIRE_DATAFILE_SIZES = False
        settings.REQUIRE_DATAFILE_CHECKSUMS = False
        self.datafile = DataFile(dataset=self.dataset1, filename='test.txt')
        self.datafile.save()
        response = self.api_client.get('/api/v1/search_simple-search/?query=test',
                                       authentication=self.get_credentials())

        data = json.loads(response.content)
        self.assertEqual(len(data['objects'][0]['hits']['experiments']), 1)
        self.assertEqual(len(data['objects'][0]['hits']['datasets']), 1)
        self.assertEqual(len(data['objects'][0]['hits']['datafiles']), 1)
