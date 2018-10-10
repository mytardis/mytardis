'''
Deprecation warnings
'''
import warnings

warnings.simplefilter('always', category=DeprecationWarning)
# warnings.simplefilter('always', category=PendingDeprecationWarning)


class RemovedInMyTardis42Warning(PendingDeprecationWarning):
    '''
    Used to raise warnings about deprecated functionality.

    Usage::

      import warnings

      warnings.warn(
          "This method will be removed in MyTardis 4.2. "
          "Please use method2 instead.",
          RemovedInMyTardis42Warning
      )
    '''
    pass


class RemovedInMyTardis41Warning(DeprecationWarning):
    '''
    Used to raise warnings about deprecated functionality.

    Usage::

      import warnings

      warnings.warn(
          "This method will be removed in MyTardis 4.1. "
          "Please use method2 instead.",
          RemovedInMyTardis41Warning
      )
    '''
    pass
