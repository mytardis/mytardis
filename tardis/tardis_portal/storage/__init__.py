from django.core.files.storage import Storage

from .file_system import MyTardisLocalFileSystemStorage

default_storage = MyTardisLocalFileSystemStorage()


class DummyStorage(Storage):
    '''Does nothing except serve as a place holder for Storage classes not
    implemented yet
    '''
