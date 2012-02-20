from django.db import models
from django.test import TestCase

from tardis.apps.sync.fields import FSMField, State, FinalState, transition_on_success


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

