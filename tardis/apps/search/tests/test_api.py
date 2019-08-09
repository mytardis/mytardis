import os
import unittest

from django.test import TestCase, modify_settings, override_settings
from django.core.management import call_command
from django.contrib.auth.models import User
from django.utils.six import StringIO
from django.test.client import Client

from tardis.tardis_portal.models import Experiment, Dataset, DataFile

from tardis.tardis_portal.tests.api import MyTardisResourceTestCase


@override_settings(SINGLE_SEARCH_ENABLED=True)
@modify_settings(INSTALLED_APPS={
    'append': 'django_elasticsearch_dsl'
})
@override_settings(ELASTICSEARCH_DSL={
        'default': {
            'hosts': 'http://localhost:9200'
        },
})
class SimpleSearchTestCase(TestCase):
    def setUp(self):
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)
        self.out = StringIO()
        call_command('search_index', stdout=self.out,
                     action='delete', force=True)
        self.exp1 = Experiment(title='test exp1',
                               institution_name='monash',
                               description='Test Description',
                               created_by=self.user)
        self.exp1.save()

    def test_simple_search(self):
        client = Client()
        client.login(username=self.user.username, password=self.user.password)
        response = client.post('/api/v1/search_advance-search/schema/')
        self.assertEqual(response.status_code, 200)
