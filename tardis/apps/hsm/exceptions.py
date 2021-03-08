"""
Exceptions related to Hierarchical Storage Management (HSM)
"""

class HsmException(Exception):
    """Base class for other exceptions to inherit from"""


class DataFileObjectNotVerified(HsmException):
    """Exception raied when an operation is attempted on an
    unverified DataFile"""


class StorageClassNotSupportedError(HsmException):
    """Exception raised when a storage class is not supported"""
