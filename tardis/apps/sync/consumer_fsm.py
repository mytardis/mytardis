from tardis.apps.sync.fields import State, FinalState, FSMField, \
        map_return_to_transition, true_false_transition
from .transfer_service import TransferService, TransferClient
from .integrity import IntegrityCheck
from .signals import transfer_completed, transfer_failed


class FailPermanent(FinalState):
    def _on_entry(self, experiment):
        transfer_failed.send_robust(sender=experiment.__class__, instance=experiment)


class Complete(FinalState):
    def _on_entry(self, experiment):
        transfer_completed.send_robust(sender=experiment.__class__, instance=experiment)


class StatusCheckState(State):
    transitions = {
        TransferService.TRANSFER_COMPLETE: 'CheckingIntegrity',
        TransferService.TRANSFER_IN_PROGRESS: 'InProgress',
        TransferService.TRANSFER_FAILED: 'FailPermanent'
    }

    @map_return_to_transition(transitions)
    def _check_status(self, experiment):
        status_dict = TransferClient().get_status(experiment)
        code = status_dict['status']
        return code

    def _get_next_state(self, experiment):
        return self._check_status(experiment)


class CheckingIntegrity(State):
    @true_false_transition(Complete, FailPermanent)
    def _get_next_state(self, experiment):
        complete = IntegrityCheck(experiment.experiment).all_files_complete()
        return complete


class InProgress(StatusCheckState):
    pass


class Requested(StatusCheckState):
    pass


class Ingested(State):
    def _ingestion_complete(self, experiment):
        return True

    @true_false_transition('Requested', 'FailPermanent')
    def _request_files(self, exp):
        return TransferClient().request_file_transfer(exp)

    def _get_next_state(self, experiment):
        if self._ingestion_complete(experiment):
            return self._request_files(experiment)
        return self


class ConsumerFSMField(FSMField):

    # TODO dynamically generate this list using metaclass
    states = {
    'Ingested' : Ingested, 
    'Requested' : Requested, 
    'InProgress' : InProgress, 
    'Complete' : Complete, 
    'CheckingIntegrity' : CheckingIntegrity, 
    'FailPermanent' : FailPermanent, 
    }

