from django.core.files.storage import FileSystemStorage


class HsmFileSystemStorage(FileSystemStorage):
    '''
    This storage class is used to describe Hierarchical Storage Management
    filesystems where files may be offline (only or tape), but can be
    recalled to disk on demand
    '''
