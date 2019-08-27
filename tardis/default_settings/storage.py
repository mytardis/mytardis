from os import path

DEFAULT_STORAGE_BASE_DIR = path.abspath(path.join(path.dirname(__file__),
                                        '../../var/store/')).replace('\\', '/')

# LEGACY, ignore
FILE_STORE_PATH = DEFAULT_STORAGE_BASE_DIR
INITIAL_LOCATIONS = {}  # keep around for old migrations

REQUIRE_DATAFILE_CHECKSUMS = True
REQUIRE_DATAFILE_SIZES = True
REQUIRE_VALIDATION_ON_INGESTION = True
COMPUTE_MD5 = True
COMPUTE_SHA512 = False

CALCULATE_CHECKSUMS_METHODS = {
}
'''
A custom method can be provided for calculating checksums for a storage class,
e.g.

CALCULATE_CHECKSUMS_METHODS = {
    'storages.backends.s3boto3.S3Boto3Storage':
        'tardis.apps.s3utils.utils.calculate_checksums'
}

The DataFileObject class's calculate_checksums method checks for a storage class
match in the CALCULATE_CHECKSUMS_METHODS dict, and if one is not found, it calls
the classic compute_checksums method which uses the file_object to calculate the
checksums one chunk at a time.  For some storage backends (e.g. S3), representing
the file as file-like object with Django's file storage API is not the most
efficient way to calculate the checksum.
'''

DEFAULT_FILE_STORAGE = \
    'tardis.tardis_portal.storage.MyTardisLocalFileSystemStorage'

METADATA_STORE_PATH = DEFAULT_STORAGE_BASE_DIR
'''
storage path for image paths stored in parameters. Better to set to another
location if possible
'''
