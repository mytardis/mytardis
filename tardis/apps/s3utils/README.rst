s3utils
=======
Utilities for integrating S3 data efficiently with MyTardis.

The initial release of this app provides the ability to redirect download
requests for S3 files to the object store (after generating a pre-signed
temporary URL) which is more efficient than streaming the download via Django.

Future enhancements planned include the ability to checksum verify an S3 file
by piping its download to an md5sum subprocess instead of using the Python-based
checksum function whose chunking algorithm may clash with the S3 download's
chunking algorithm.  And for small files (not multipart uploads), it may be
possible to use an object's eTag to determine its MD5 sum.

The s3utils app can be used with the ``DOWNLOAD_URI_TEMPLATES`` setting described in
``tardis/default_settings/download.py`` to provide more efficient downloads of
objects in S3 storage backends.

To use it, add the following to your ``settings.py``::

  INSTALLED_APPS += ('tardis.apps.s3utils',)

  DOWNLOAD_URI_TEMPLATES = {
      'storages.backends.s3boto3.S3Boto3Storage': '/api/v1/s3utils_replica/{dfo_id}/download/'
  }
