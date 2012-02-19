from django.db import models



class State(object):
    
    def __unicode__(self):
        return "%s" % (self.__class__.__name__)
    
    def __str__(self):
        return "%s" % (self.__class__.__name__)

    def get_next_state(self):
        return self

    def is_final_state(self):
        return False

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
                if ret == False:
                    #sys.stderr.write("retrun false")
                    return self
            except Exception, e:
                #sys.stderr.write("exception: %s" % (e))
                # return the current state
                return self
            return state()
        return wrap_f
    return wrap

