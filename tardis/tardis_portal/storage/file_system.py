from django.conf import settings
from django.core.files.storage import FileSystemStorage


class MyTardisLocalFileSystemStorage(FileSystemStorage):
    """
    Simply changes the FileSystemStorage default store location to the MyTardis
    file store location. Makes it easier to migrate 2.5 installations.
    """

    def __init__(self, location=None, base_url=None):
        if location is None:
            location = getattr(
                settings, "DEFAULT_STORAGE_BASE_DIR", "/var/lib/mytardis/store"
            )
        super().__init__(location, base_url)
