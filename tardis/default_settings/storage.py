from os import path

DEFAULT_STORAGE_BASE_DIR = path.abspath(path.join(path.dirname(__file__),
                                        '../../var/store/')).replace('\\', '/')

# LEGACY, ignore
FILE_STORE_PATH = DEFAULT_STORAGE_BASE_DIR
INITIAL_LOCATIONS = {}  # keep around for old migrations
REQUIRE_DATAFILE_CHECKSUMS = True
REQUIRE_DATAFILE_SIZES = True
REQUIRE_VALIDATION_ON_INGESTION = True

DEFAULT_FILE_STORAGE = \
    'tardis.tardis_portal.storage.MyTardisLocalFileSystemStorage'

METADATA_STORE_PATH = DEFAULT_STORAGE_BASE_DIR
'''
storage path for image paths stored in parameters. Better to set to another
location if possible
'''
