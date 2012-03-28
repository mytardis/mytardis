from flexmock import flexmock
from django.test import TestCase
from django.dispatch import receiver

from tardis.tardis_portal.models import Experiment

from tardis.apps.sync.consumer_fsm import Complete, InProgress, FailPermanent, \
        CheckingIntegrity, Requested, Ingested
from tardis.apps.sync.tasks import clock_tick
from tardis.apps.sync.models import SyncedExperiment
from ..transfer_service import TransferClient, TransferService
from ..integrity import IntegrityCheck
from ..signals import transfer_failed, transfer_completed

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
                public_access = Experiment.PUBLIC_ACCESS_FULL
                )
        self.uid = 0
        self.url = 'http://remotetardis:8080'

        self.mock_ts = flexmock()
        flexmock(TransferClient).new_instances(self.mock_ts)

        self.mock_integrity = flexmock()
        flexmock(IntegrityCheck).new_instances(self.mock_integrity)

        self.status = {
                'human_status': 'this is a readable status',
                'message': 'this is a message'
                }

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
        print 'Old state ->', initial_state()
        print 'New state ->', new.state
        print 'Expected  ->', expected_state(),
        self.assertIsInstance(new.state, expected_state)

    def _mock_get_status(self, status):
        self.status['status'] = status
        return self.mock_ts.should_receive('get_status').and_return(self.status).once

    # Positive transitions (everything is excellent all the time)

    def testGetsNewEntries(self):
        self.mock_ts.should_receive('request_file_transfer').and_return(True).once
        self.transitionCheck(Ingested, Requested)

    def testRequestedTransferNowInProgress(self):
        self._mock_get_status(TransferService.TRANSFER_IN_PROGRESS)
        self.transitionCheck(Requested, InProgress)

    def testRequestedTransferCompletesInstantly(self):
        self._mock_get_status(TransferService.TRANSFER_COMPLETE)
        self.transitionCheck(Requested, CheckingIntegrity)

    def testWaitsForTransferCompletion(self):
        self._mock_get_status(TransferService.TRANSFER_IN_PROGRESS)
        self.transitionCheck(InProgress, InProgress)

    def testChecksIntegrityAfterTransferCompletion(self):
        self._mock_get_status(TransferService.TRANSFER_COMPLETE)
        self.transitionCheck(InProgress, CheckingIntegrity)

    def testCompleteAfterIntegrityCheckPasses(self):
        self.mock_ts.should_receive('get_status').never
        self.mock_integrity.should_receive('all_files_complete').and_return(True).once
        self.transitionCheck(CheckingIntegrity, Complete)

    def testSendsSignalOnComplete(self):
        @receiver(transfer_completed)
        def transfer_complete(sender, **kwargs):
            self.instance = kwargs['instance']
        self.mock_integrity.should_receive('all_files_complete').and_return(True).once
        self.transitionCheck(CheckingIntegrity, Complete)
        self.assertIsInstance(self.instance, SyncedExperiment)

    def testSkipsCompleteEntries(self):
        self.mock_ts.should_receive('get_status').never
        self.transitionCheck(Complete, Complete)

    def testSkipsFailedEntries(self):
        self.mock_ts.should_receive('get_status').never
        self.transitionCheck(FailPermanent, FailPermanent)

    # Negative results (currently going start to FailPermanent)

    def testTransferRequestFailed(self):
        self.mock_ts.should_receive('request_file_transfer').and_return(False).once
        self.transitionCheck(Ingested, FailPermanent)

    def testTransferNotStarted(self):
        # We may need a TRANSFER_REQUEST_RECEIVED or TRANSFER_STARTED
        self._mock_get_status(TransferService.TRANSFER_FAILED)
        self.transitionCheck(Requested, FailPermanent)

    def testInProgressTransferFailed(self):
        self._mock_get_status(TransferService.TRANSFER_FAILED)
        self.transitionCheck(InProgress, FailPermanent)

    def testSendsSignalOnFailure(self):
        @receiver(transfer_failed)
        def transfer_fail(sender, **kwargs):
            self.instance = kwargs['instance']
        self._mock_get_status(TransferService.TRANSFER_FAILED)
        self.transitionCheck(InProgress, FailPermanent)
        self.assertIsInstance(self.instance, SyncedExperiment)

    def testIntegrityCheckFailed(self):
        self.mock_integrity.should_receive('all_files_complete').and_return(False).once
        self.transitionCheck(CheckingIntegrity, FailPermanent)

