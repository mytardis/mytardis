from django.core.management import call_command
from django.contrib.auth.models import User
from django.utils.six import StringIO
from django.test import TestCase

from tardis.tardis_portal.models import Dataset, Experiment

from ..documents import ExperimentDocument


class IndexExperimentTestCase(TestCase):

    def setUp(self):
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)
        self.out = StringIO()
        call_command('search_index', stdout=self.out,
                     action='delete', models=['tardis_portal.experiment'], force=True)

    def test_create_index(self):
        exp1 = Experiment(title='test exp1',
                                institution_name='monash',
                                description='Test Description',
                                created_by=self.user)
        exp2 = Experiment(title='test exp2',
                                institution_name='monash',
                                description='Test Description',
                                created_by=self.user)
        exp1.save()
        exp2.save()
        # get search instance
        search = ExperimentDocument.search()
        # query for title(exact matching)
        query = search.query("match", title='test exp1')
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].title, 'test exp1')
        # query for description
        query = search.query("match", description='Test Description')
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].description, 'Test Description')
        # query for created_time
        query = search.query("match", created_time=exp1.created_time)
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].created_time, exp1.created_time)
