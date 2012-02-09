from tardis.apps.sync.fields import State, transition_on_success, FSMField

class InProgress(State):

    def get_next_state(self, experiment):
        return self;

class Requested(State):

    def _check_transfer_started(self, experiment):
        return True
    
    @transition_on_success(InProgress)
    def _wait(self, experiment):
        return True
    
    def get_next_state(self, experiment):
       
        started = self._check_transfer_started(experiment)

        if started:
           return self._wait(experiment)
        return self

class Ingesting(State):

    def _check_ingestion_complete(self, experiment):
        return True
        
    @transition_on_success(Requested)
    def _request_files(self):
        pass
    
    def get_next_state(self, experiment):

        complete = self._check_ingestion_complete(experiment)
        
        if complete:
            return self._request_files()
        return self

class ConsumerFSMField(FSMField):

    # TODO dynamically generate this list using metaclass
    FSMField.states = {
    'Ingesting' : Ingesting, 
    'Requested' : Requested, 
    'InProgress' : InProgress, 
    }
