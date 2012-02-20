from flexmock import flexmock
from django.test import TestCase

from tardis.tardis_portal.models import Experiment

from tardis.apps.sync.consumer_fsm import Complete, InProgress, FailPermanent, \
        CheckingIntegrity, Requested
from tardis.apps.sync.tasks import clock_tick
from tardis.apps.sync.models import SyncedExperiment
from ..transfer_service import TransferClient, TransferService

from django.contrib.auth.models import User


class consumerFSMTestCase(TestCase):

    def load_test_stub(self):
        pass

    def setUp(self):
        pass

    def finishes_on_hard_fail(func):
        pass

    def finishes_on_complete(func):
        pass

    @finishes_on_complete
    def testRegularProgression(self):
        pass

    @finishes_on_hard_fail
    def testTranferFailure(self):
        pass

    @finishes_on_hard_fail
    def testHardFail(self):
        pass


class ClockTestCase(TestCase):

    def setUp(self):

        self.user = User(username='user1', password='password', email='a@a.com')
        self.user.save()
        self.exp = Experiment(
                approved = True,
                title = 'title1',
                institution_name = 'institution1',
                description = 'description1',
                created_by = self.user,
                public = True
                )
        self.uid = 0
        self.url = 'http://remotetardis:8080'

        mock = flexmock()
        flexmock(TransferClient).new_instances(mock)
        mock.should_receive('get_status').and_return(
                { 'status': TransferService.TRANSFER_IN_PROGRESS })


    def testGetsNewEntries(self):
        self.exp.id = 0
        self.exp.save()
        self.in_progress = SyncedExperiment(
                experiment=self.exp, uid=self.uid, provider_url=self.url)
        self.uid += 1

        self.in_progress.state = Requested()
        self.in_progress.save()
        clock_tick()

        new = SyncedExperiment.objects.all()[0]
        self.assertTrue(isinstance(new.state, InProgress))

    def testSkipsCompleteEntries(self):
        self.exp.id = 0
        self.exp.save()
        self.finished = SyncedExperiment(
                experiment=self.exp, uid=self.uid, provider_url=self.url)
        self.uid += 1
        self.finished.state = Complete()
        self.finished.save()

        clock_tick()

        new = SyncedExperiment.objects.all()[0]
        self.assertTrue(isinstance(new.state, Complete))

    def testSkipsFailedEntries(self):
        self.exp.id = 0
        self.exp.save()
        self.failed = SyncedExperiment(
                experiment=self.exp, uid=self.uid, provider_url=self.url)
        self.uid += 1
        self.failed.state = FailPermanent()
        self.failed.save()

        clock_tick()

        new = SyncedExperiment.objects.all()[0]
        self.assertTrue(isinstance(new.state, FailPermanent))

