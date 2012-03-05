import logging
from django.db import models


logger = logging.getLogger(__name__)


class State(object):
    def __unicode__(self):
        return "%s" % (self.__class__.__name__)
    
    def __str__(self):
        return "%s" % (self.__class__.__name__)

    def get_next_state(self, *args, **kwargs):
        next_state = self._get_next_state(*args, **kwargs)
        if self.__class__.__name__ != next_state.__class__.__name__:
            self._on_exit(*args, **kwargs)
            next_state._on_entry(*args, **kwargs)
            return next_state
        return self

    def is_final_state(self):
        return False

    def _get_next_state(self):
        raise NotImplementedError()

    def _on_entry(self, *args, **kwargs):
        pass

    def _on_exit(self, *args, **kwargs):
        pass


class FinalState(State):
    def is_final_state(self):
        return True


class FSMField(models.Field):
                    
    __metaclass__ = models.SubfieldBase

    states = {}

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 50)
        super(FSMField, self).__init__(*args, **kwargs)
    
    def to_python(self, value):
        if isinstance(value, State):
            return value
        return self.__class__.states.get(str(value))()
    
    def get_prep_value(self, value):
        return str(value)

    def get_internal_type(self):
        return 'CharField'

# TODO move condition checking to the decorator
def transition_on_success(state, conditions=[]):
    def wrap(f):
        def wrap_f(*args):
            self = args[0]
            #sys.stderr.write("starting: %s" % (state))
            #sys.stderr.write("self: %s" % (self))
            try:
                ret = f(*args)
            except Exception, e:
                logger.exception('transition_on_success:')
                # return the current state
                return self
            if ret == False:
                #sys.stderr.write("retrun false")
                return self
            return state()
        return wrap_f
    return wrap


def true_false_transition(true_state, false_state):
    def wrap(f):
        def wrap_f(*args):
            self = args[0]
            #sys.stderr.write("starting: %s" % (state))
            #sys.stderr.write("self: %s" % (self))
            try:
                ret = f(*args)
                new_state = true_state if ret else false_state
            except Exception, e:
                logger.exception('true_false_transition:')
                # return the current state
                new_state = false_state
            if isinstance(new_state, str):
                module = __import__(self.__class__.__module__,
                        globals(), locals(), [new_state])
                return getattr(module, new_state)()
            return new_state()
        return wrap_f
    return wrap


def map_return_to_transition(conditions):
    def wrap(f):
        def wrap_f(*args):
            self = args[0]
            #sys.stderr.write("starting: %s" % (state))
            #sys.stderr.write("self: %s" % (self))
            try:
                ret = f(*args)
            except Exception, e:
                logger.exception('map_return_to_transition:')
                # return the current state
                return self
            new_state = conditions.get(ret, None)
            if new_state is None:
                return self
            if isinstance(new_state, str):
                module = __import__(self.__class__.__module__,
                        globals(), locals(), [new_state])
                return getattr(module, new_state)()
            return new_state()
        return wrap_f
    return wrap

