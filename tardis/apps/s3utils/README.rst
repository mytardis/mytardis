s3utils
=======

The s3utils app can be used with the ``DOWNLOAD_URI_TEMPLATES`` setting described in
``tardis/default_settings/download.py`` to provide more efficient downloads of
objects in S3 storage backends.

To use it, add the following to your ``settings.py``::

  INSTALLED_APPS += ('tardis.apps.s3utils',)

  DOWNLOAD_URI_TEMPLATES = {
      'storages.backends.s3boto3.S3Boto3Storage': '/api/v1/s3utils_replica/{dfo_id}/download/'
  }
