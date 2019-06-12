'''
Tests related to Search  views
'''

import unittest
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.test.client import Client
from django.utils.six import StringIO
from django.contrib.auth.models import User

from tardis.tardis_portal.models import Experiment, Dataset, DataFile


class SearchViewTestCase(TestCase):
    @unittest.skipUnless(
        getattr(settings, 'ELASTICSEARCH_DSL', False),
        "--elasticsearch not set"
    )
    def setUp(self):
        self.client = Client()
        self.out = StringIO()
        call_command('search_index', stdout=self.out,
                     action='delete',
                     models=['tardis_portal.experiment', 'tardis_portal.dataset', 'tardis_portal.datafile'],
                     force=True)
        user_username = 'tardis_user1'
        pwd = 'secret'
        email = 'tadis@tardis.com'
        self.user = User.objects.create_user(user_username, email, pwd)
        # create Experiment, Dataset, and Datafile
        self.exp = Experiment(title='test exp',
                               institution_name='monash',
                               description='Test Description',
                               created_by=self.user)
        self.exp.save()
        self.dataset = Dataset(description='Test dataset')
        self.dataset.save()
        self.dataset.experiments.add(self.exp)
        self.dataset.save()
        settings.REQUIRE_DATAFILE_SIZES = False
        settings.REQUIRE_DATAFILE_CHECKSUMS = False
        self.datafile = DataFile(dataset=self.dataset, filename='test.txt')
        self.datafile.save()

    def test_simple_search_view(self):
        client = Client()
        response = client.get('/apps/search-v2/%3F?q=test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['hits'].total, 2)
