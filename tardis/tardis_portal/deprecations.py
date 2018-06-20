'''
Deprecation warnings
'''
import warnings

warnings.simplefilter('always', category=DeprecationWarning)


class RemovedInMyTardis40Warning(DeprecationWarning):
    '''
    Used to raise warnings about deprecated functionality.

    Usage:

    import warnings

    warnings.warn(
        "This method will be removed in MyTardis 4.0. "
        "Please use method2 instead.",
        RemovedInMyTardis40Warning
    )
    '''
    pass
