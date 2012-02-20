from flexmock import flexmock
from django.test import TestCase

from tardis.tardis_portal.models import Experiment

from tardis.apps.sync.consumer_fsm import Complete, InProgress, FailPermanent, \
        CheckingIntegrity, Requested, Ingested
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
        self.mock = mock

    def transitionCheck(self, initial_state, expected_state):
        self.exp.id = 0
        self.exp.save()
        exp = SyncedExperiment(
                experiment=self.exp, uid=self.uid, provider_url=self.url)
        self.uid += 1
        exp.state = initial_state()
        exp.save()

        clock_tick()

        new = SyncedExperiment.objects.all()[0]
        self.assertTrue(isinstance(new.state, expected_state))

    # Positive transitions (everything is excellent all the time)

    def testIngestedToRequested(self):
        self.mock.should_receive('request_file_transfer').and_return(True)
        self.transitionCheck(Ingested, Requested)

    def testGetsNewEntries(self):
        self.mock.should_receive('get_status').and_return(
                { 'status': TransferService.TRANSFER_IN_PROGRESS })
        self.transitionCheck(Requested, InProgress)

    def testWaitsForTransferCompletion(self):
        self.mock.should_receive('get_status').and_return(
                { 'status': TransferService.TRANSFER_IN_PROGRESS })
        self.transitionCheck(InProgress, InProgress)

    def testChecksIntegrityAfterTransferCompletion(self):
        self.mock.should_receive('get_status').and_return(
                { 'status': TransferService.TRANSFER_COMPLETE })
        self.transitionCheck(InProgress, CheckingIntegrity)

    def testCompleteAfterIntegrityCheckPasses(self):
        self.mock.should_receive('get_status').never
        # Integrity check here
        self.transitionCheck(CheckingIntegrity, Complete)

    def testSkipsCompleteEntries(self):
        self.mock.should_receive('get_status').never
        self.transitionCheck(Complete, Complete)

    def testSkipsFailedEntries(self):
        self.mock.should_receive('get_status').never
        self.transitionCheck(FailPermanent, FailPermanent)

    # Negative results
