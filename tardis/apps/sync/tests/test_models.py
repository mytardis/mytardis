import json

from django.test import TestCase
from django.contrib.auth.models import User

from tardis.tardis_portal.models import Experiment
from tardis.apps.sync.models import SyncedExperiment


class ModelsTestCase(TestCase):

    def setUp(self):
        self.user = User(username='user1', password='password', email='a@a.com')
        self.user.save()
        self.exp = Experiment(
                approved = True,
                title = 'title1',
                institution_name = 'institution1',
                description = 'description1',
                created_by = self.user,
                public_access = Experiment.PUBLIC_ACCESS_FULL
                )
        self.exp.save()
        self.uid = 0
        self.url = 'http://remotetardis:8080'

    def testGetEmptyStatus(self):
        exp = SyncedExperiment(
                experiment=self.exp, uid=self.uid, provider_url=self.url)
        exp.save()
        d = exp.status()
        self.assertEqual(d, None)

    def testGetStatus(self):
        json_str = '{"key": "value"}'
        exp = SyncedExperiment(
                experiment=self.exp, uid=self.uid, provider_url=self.url)
        exp.msg = json_str
        exp.save()
        d = exp.status()
        self.assertIsInstance(d, dict)
        self.assertEqual(d['key'], 'value')

    def testSetStatus(self):
        d = { "key": "value" }
        exp = SyncedExperiment(
                experiment=self.exp, uid=self.uid, provider_url=self.url)
        exp.save()
        exp.save_status(d)
        json_d = json.loads(exp.msg)
        self.assertEqual(d, json_d)

