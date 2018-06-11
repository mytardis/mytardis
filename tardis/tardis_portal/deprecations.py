'''
Deprecation warnings
'''
import warnings

warnings.simplefilter('always')


class RemovedInMyTardis310Warning(PendingDeprecationWarning):
    '''
    Used to raise warnings about deprecated functionality.

    Usage:

    import warnings

    warnings.warn(
        "This method will be removed in MyTardis 3.10. "
        "Please use method2 instead.",
        RemovedInMyTardis310Warning
    )
    '''
    pass


class RemovedInMyTardis39Warning(DeprecationWarning):
    '''
    Used to raise warnings about deprecated functionality.

    Usage:

    import warnings

    warnings.warn(
        "This method will be removed in MyTardis 3.9. "
        "Please use method2 instead.",
        RemovedInMyTardis39Warning
    )
    '''
    pass
