# for transition only:
from .file_system import MyTardisLocalFileSystemStorage

default_storage = MyTardisLocalFileSystemStorage()


class MisconfiguredStorageError(Exception):
    pass
