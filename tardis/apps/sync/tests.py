"""
"""
from django.test import TestCase
from django.db import models
from django.contrib.auth.models import User
from tardis.apps.sync.fields import FSMField, State, FinalState, transition_on_success
from tardis.apps.sync.tasks import clock_tick
from tardis.apps.sync.consumer_fsm import Complete, InProgress, FailPermanent, \
        CheckingIntegrity, Requested
from tardis.apps.sync.models import SyncedExperiment

class DontCloseTheDoor(Exception):
    pass

class WalkingTheDinosaur(FinalState):
    
    def is_final_state(self):
        return True
    def get_next_state(self):
        return self

class ReallyOnTheFloor(FinalState):
    
    def get_next_state(self):
        return ReallyOnTheFloor

class OnTheFloor(State):
    
    @transition_on_success(ReallyOnTheFloor)
    def _get_on_floor_more(self):
        return False

    @transition_on_success(WalkingTheDinosaur)
    def _walk_the_dinosaur(self):
        return True

    def get_next_state(self):
        transition = self._get_on_floor_more()

        if not transition == self:
            return transition

        transition = self._walk_the_dinosaur()
        return transition

class DoorClosed(State):
    pass

class DoorOpen(State):
    
    @transition_on_success(DoorClosed)
    def _close_door(self):
        raise DontCloseTheDoor()

    @transition_on_success(OnTheFloor)
    def _get_on_the_floor(self):
        return True

    def get_next_state(self):

        transition =  self._close_door()

        if not transition == self:
            return transition

        transition = self._get_on_the_floor()
        return transition

class DoingNothing(State):
    @transition_on_success(DoorOpen)
    def _open_the_door(self):
        return True

    def get_next_state(self):
        return self._open_the_door()

class FSMTestCase(TestCase):

    # TODO: The return true bit is misleading
    @transition_on_success(CheckingIntegrity)
    def _complete(self, experiment):
        return True
    
    def get_next_state(self, experiment):
        return self._complete(experiment)
   
    def setup(self):
        pass

    def testRegularProgression(self):
        state = DoingNothing()
        state = state.get_next_state()
        self.assertTrue(isinstance(state, DoorOpen))
        state = state.get_next_state()
        self.assertTrue(isinstance(state, OnTheFloor))
        state = state.get_next_state()
        self.assertTrue(isinstance(state, WalkingTheDinosaur))
        state = state.get_next_state()
        self.assertTrue(isinstance(state, WalkingTheDinosaur))
        self.assertTrue(state.is_final_state())

    def testKnownStateTransitionSucceeds(self):
        state = DoingNothing()
        state = state.get_next_state()
        self.assertTrue(isinstance(state, DoorOpen))
    
    def testNoTransitionOnFailure(self):
        state = OnTheFloor() 
        state = state._get_on_floor_more()
        self.assertTrue(isinstance(state, OnTheFloor))

    def testNoTransitionOnException(self):
        state = DoorOpen() 
        state = state._close_door()
        self.assertTrue(isinstance(state, DoorOpen))

    def testFinalStateReportsCorrectly(self):

        state = WalkingTheDinosaur()
        self.assertTrue(state.is_final_state())

        state = ReallyOnTheFloor()
        self.assertTrue(state.is_final_state())

        state = OnTheFloor()
        state = state.get_next_state()
        self.assertTrue(isinstance(state, WalkingTheDinosaur))
        self.assertTrue(state.is_final_state())


class WasNotWasFSMField(FSMField):
    states = {
            'DoingNothing' : DoingNothing,
            'DoorOpen' : DoorOpen,
            'OnTheFloor' : OnTheFloor,
            'WalkingTheDinosaur' : WalkingTheDinosaur,
            'DoorClosed' : DoorClosed,
            'ReallyOnTheFloor' : ReallyOnTheFloor,
            }


class Everybody(models.Model):
    state = WasNotWasFSMField(default='DoingNothing')

class FSMFieldTestCase(TestCase):
    
    def testSetGet(self):
        ev = Everybody()
        ev.state = OnTheFloor()
        self.assertTrue(isinstance(ev.state, OnTheFloor))

        ev.state = ev.state.get_next_state()
        self.assertTrue(isinstance(ev.state, WalkingTheDinosaur))

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

    def testGetsNewEntries(self):

        self.in_progress = SyncedExperiment(
                url ="www.in_progress.com", 
                approved = True,
                title = 'title1',
                institution_name = 'institution1',
                description = 'description1',
                created_by = self.user,
                public = True 
                )

        self.in_progress.state = Requested()
        self.in_progress.save()
        clock_tick()

        new = SyncedExperiment.objects.all()[0]
        self.assertTrue(isinstance(new.state, InProgress))
            
    def testSkipsCompleteEntries(self):
        
        self.finished = SyncedExperiment(
                url ="www.finished.com", 
                approved = True,
                title = 'title2',
                institution_name = 'institution2',
                description = 'description2', 
                created_by = self.user,
                public = True 
                )
        self.finished.state = Complete()
        self.finished.save()

        clock_tick()

        new = SyncedExperiment.objects.all()[0]
        self.assertTrue(isinstance(new.state, Complete))

    def testSkipsFailedEntries(self):

        self.failed = SyncedExperiment(
                url ="www.failed.com", 
                approved = True,
                title = 'title3',
                institution_name = 'institution3', 
                description = 'description3', 
                created_by = self.user,
                public = True 
                )
        
        self.failed.state = FailPermanent()
        self.failed.save()

        clock_tick()

        new = SyncedExperiment.objects.all()[0]
        self.assertTrue(isinstance(new.state, FailPermanent))

class ManagerTestCase(TestCase):

    def uidGeneration(self):
        pass

class GetExperimentViewTestCase(TestCase):

    def testDefaultBackendLoads(self):
        pass

    def testCustomBackendLoads(self):
        pass




