'''
Deprecation warnings
'''
import warnings

warnings.simplefilter('always', category=DeprecationWarning)
warnings.simplefilter('always', category=PendingDeprecationWarning)


class RemovedInMyTardis311Warning(PendingDeprecationWarning):
    '''
    Used to raise warnings about deprecated functionality.

    Usage:

    import warnings

    warnings.warn(
        "This method will be removed in MyTardis 3.11. "
        "Please use method2 instead.",
        RemovedInMyTardis311Warning
    )
    '''
    pass


class RemovedInMyTardis310Warning(DeprecationWarning):
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
