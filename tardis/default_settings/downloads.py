DOWNLOAD_PATH_MAPPERS = {
    'deep-storage': (
        'tardis.apps.deep_storage_download_mapper.mapper.deep_storage_mapper',
    ),
}

# Site's default archive organization (i.e. path structure)
DEFAULT_PATH_MAPPER = 'deep-storage'

# Don't percent-encode characters in the SAFE_FILESYSTEM_CHARACTERS
# string when creating TARs and SFTP views.
#
# There is a difference between filesystem-safe and shell-safe.
# For example, in bash, we can create a file:
#
# touch ' !#$&'\''()+;,:=@[]'
#
# and then create a TAR containing that file:
#
# tar cf test.tar ' !#$&'\''()+;,:=@[]'
#
# and then remove the file and recreate it by extracting it from the TAR:
#
# rm ' !#$&'\''()+;,:=@[]'
# tar xvf test.tar
#
# Extracting the file from the TAR archive alone is not dangerous, but the
# filename could be considered dangerous for novice shell users or for
# developers prone to introducing shell-injection vulnerabilities:
# https://en.wikipedia.org/wiki/Code_injection#Shell_injection
#
# SAFE_FILESYSTEM_CHARACTERS = " !#$&'()+,:;=@[]"
SAFE_FILESYSTEM_CHARACTERS = ""

# Convert experiment title spaces to underscores in TARs and SFTP:
EXP_SPACES_TO_UNDERSCORES = True

# Convert dataset description spaces to underscores in TARs and SFTP:
DATASET_SPACES_TO_UNDERSCORES = True

DEFAULT_ARCHIVE_FORMATS = ['tar']
'''
Site's preferred archive types, with the most preferred first
other available option: 'tgz'. Add to list if desired
'''

DOWNLOAD_URI_TEMPLATES = {}
'''
When a file download is requested, by default, MyTardis will create
a StreamingHttpResponse to serve the download which requires reading
the file from a file-like object.  For some storage backends, e.g.
S3Boto3Storage provided by the django-storages package, it is more
efficient to redirect the request directly to the storage provider.

Or the download request could be handled by an API which is aware
of HSM (Hierarchical Storage Management) status for files which
could be either on disk or on tape.

The DOWNLOAD_URI_TEMPLATES dictionary can be used to specify a URI
template (e.g. '/api/v1/s3utils_replica/{dfo_id}/download/'
which can be used to download a DataFileObject, instead of using
the default /api/v1/dataset_file/[datafile_id]/download/ endpoint.

For example,

  DOWNLOAD_URI_TEMPLATES = {
      'storages.backends.s3boto3.S3Boto3Storage':
      '/api/v1/s3utils_replica/{dfo_id}/download/'
  }

The '/api/v1/s3utils_replica/{dfo_id}/download/' endpoint is provided
by the 's3utils' tardis app which needs to be in your INSTALLED_APPS
'''
