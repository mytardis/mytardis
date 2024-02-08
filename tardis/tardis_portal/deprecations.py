"""
Deprecation warnings
"""
import warnings

warnings.simplefilter("always", category=DeprecationWarning)
# warnings.simplefilter('always', category=PendingDeprecationWarning)


class RemovedInMyTardis43Warning(PendingDeprecationWarning):
    """
    Used to raise warnings about deprecated functionality.

    Usage::

      import warnings

      warnings.warn(
          "This method will be removed in MyTardis 4.3. "
          "Please use method2 instead.",
          RemovedInMyTardis43Warning
      )
    """


class RemovedInMyTardis42Warning(DeprecationWarning):
    """
    Used to raise warnings about deprecated functionality.

    Usage::

      import warnings

      warnings.warn(
          "This method will be removed in MyTardis 4.2. "
          "Please use method2 instead.",
          RemovedInMyTardis42Warning
      )
    """
