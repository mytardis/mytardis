from tardis.apps.sync.fields import State, FinalState, FSMField, \
        map_return_to_transition, true_false_transition
from transfer_service import TransferService, TransferClient

from .integrity import IntegrityCheck
from .signals import transfer_completed, transfer_failed



def _check_status(experiment):
    status_dict = TransferClient().get_status(experiment)
    code = status_dict['status']
    experiment.msg = '%s: %s' % (status_dict['human_status'], status_dict['message'])
    experiment.save()
    return code


class FailPermanent(FinalState):
    def _on_entry(self, experiment):
        transfer_failed.send_robust(sender=experiment.__class__, instance=experiment)


class Complete(FinalState):
    def _on_entry(self, experiment):
        transfer_completed.send_robust(sender=experiment.__class__, instance=experiment)


class CheckingIntegrity(State):
    @true_false_transition(Complete, FailPermanent)
    def _get_next_state(self, experiment):
        complete = IntegrityCheck(experiment.experiment).all_files_complete()
        return complete


class InProgress(State):
    transitions = {
        TransferService.TRANSFER_COMPLETE: 'CheckingIntegrity',
        TransferService.TRANSFER_FAILED: 'FailPermanent'
    }

    @map_return_to_transition(transitions)
    def _get_next_state(self, experiment):
        return _check_status(experiment)


class Requested(State):
    # TODO: Investigate workflows to retry request
    transitions = {
        TransferService.TRANSFER_COMPLETE: 'CheckingIntegrity',
        TransferService.TRANSFER_IN_PROGRESS: 'InProgress',
        TransferService.TRANSFER_FAILED: 'FailPermanent'
    }

    @map_return_to_transition(transitions)
    def _get_next_state(self, experiment):
        return _check_status(experiment)


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

