from flexmock import flexmock
from django.test import TestCase
from django.contrib.auth.models import User
from nose.tools import raises

from tardis.tardis_portal.models import Experiment, ParameterName, Schema, ExperimentParameter, ExperimentParameterSet

from tardis.apps.sync.consumer_fsm import Complete, InProgress, FailPermanent, \
        CheckingIntegrity, Requested, Ingested
from tardis.apps.sync.tasks import clock_tick
from tardis.apps.sync.models import SyncedExperiment

from ..transfer_service import TransferService
from ..managers.default_manager import SyncManager
from ..site_manager import SiteManager

from httplib2 import Http

class ManagerTestCase(TestCase):
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
        self.sync_exp = SyncedExperiment(
                experiment=self.exp,
                uid='test.1',
                provider_url='http://somewhere.com')
        self.sync_exp.save()
        self.site_manager = flexmock()
        flexmock(SiteManager).new_instances(self.site_manager)
        self.Http = flexmock()
        flexmock(Http).new_instances(self.Http)


class SyncManagerTestCase(ManagerTestCase):
    def testGenerateUid(self):
        sm = SyncManager(institution='test')
        uid = sm.generate_exp_uid(self.exp)
        self.assertEqual(uid, 'test.1')

    def testExpFromUid(self):
        sm = SyncManager(institution='test')
        result = sm._exp_from_uid('test.1')
        self.assertEqual(result, self.exp)

    @raises(TransferService.InvalidUIDError)
    def testExpFromInvalidInstitution(self):
        sm = SyncManager(institution='test')
        result = sm._exp_from_uid('test1.unicorns')

    @raises(TransferService.InvalidUIDError)
    def testExpFromInvalidUid(self):
        sm = SyncManager(institution='test')
        result = sm._exp_from_uid('testunicorns')

    @raises(TransferService.InvalidUIDError)
    def testExpFromInvalidUid(self):
        sm = SyncManager(institution='test')
        result = sm._exp_from_uid('test.unicorns')

    def testGetStatus(self):
        sm = SyncManager(institution='test')
        sm.get_status('test.1')

    def testPostExperiment(self):
        sm = SyncManager(institution='test')
        settings = {
            'url': 'http://somewhere.com',
            'username': 'username',
            'password': 'password',
            'fileProtocol': 'tardis' }
        import httplib2
        resp = httplib2.Response({'status': '200'})
        self.Http.should_receive('request').with_args(settings['url'], 'POST', body=str, headers=dict).and_return((resp, ''))
        result = sm._post_experiment(self.sync_exp, [], settings)
        self.assertTrue(result)

    def testPostExperimentFailed(self):
        sm = SyncManager(institution='test')
        settings = {
            'url': 'http://somewhere.com',
            'username': 'username',
            'password': 'password',
            'fileProtocol': 'tardis' }
        import httplib2
        resp = httplib2.Response({'status': '500'})
        self.Http.should_receive('request').with_args(
                settings['url'], 'POST', body=str, headers=dict).and_return((resp, ''))
        result = sm._post_experiment(self.sync_exp, [], settings)
        self.assertFalse(result)

    def testGetStatus(self):
        sm = SyncManager(institution='test')
        result = sm.get_status('test.1')

    def testStartFileTransfer(self):
        settings = { 'transfer': { 'option1': 'option1test' } }
        self.site_manager.should_receive('get_site_settings').and_return(settings)

        sm = SyncManager(institution='test')
        sm._start_file_transfer = lambda *args: args
        url = 'http://somewhere.com'
        exp, settings_, dest_path = sm.start_file_transfer('test.1', url, 'path_to_exp')
        self.assertEqual(exp, self.exp)
        self.assertEqual(settings['transfer'], settings_)
        self.assertEqual(dest_path, 'path_to_exp')

    @raises(TransferService.SiteError)
    def testStartFileTransferInvalidSite(self):
        self.site_manager.should_receive('get_site_settings').and_return(None)

        sm = SyncManager(institution='test')
        url = 'http://somewhere.com'
        exp, settings_, dest_path = sm.start_file_transfer('test.1', url, 'path_to_exp')
