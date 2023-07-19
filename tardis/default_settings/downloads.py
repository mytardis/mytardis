DOWNLOAD_PATH_MAPPERS = {
    "deep-storage": (
        "tardis.apps.deep_storage_download_mapper.mapper.deep_storage_mapper",
    ),
}

# Site's default archive organization (i.e. path structure)
DEFAULT_PATH_MAPPER = "deep-storage"

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

DEFAULT_ARCHIVE_FORMATS = ["tar"]
"""
Site's preferred archive types, with the most preferred first
other available option: 'tgz'. Add to list if desired
"""

DOWNLOAD_URI_TEMPLATES = {}
"""
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
"""

DOWNLOAD_URI_TEMPLATES = {}
"""
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
"""

PROXY_DOWNLOADS = False
"""
Enable proxying of downloads to NGINX (or another web server)
"""

PROXY_DOWNLOAD_PREFIXES = {}
"""
The PROXY_DOWNLOAD_PREFIXES dictionary describes the mapping between
each directory prefix and the corresponding internal URL prefix:

  PROXY_DOWNLOAD_PREFIXES = {
      '/srv/': '/protected/'
  }

For downloads not handled by DOWNLOAD_URI_TEMPLATES, an alternative
to streaming the downloads from MyTardis is to proxy the download
request to NGINX using an X-Accel-Redirect header.  You can choose a
directory or mountpoint prefix e.g. '/srv/' or '/mnt/' and have MyTardis
redirect all download requests to NGINX for files within that directory.

For this to work, the NGINX worker processes need to be able to read the
data directories.  One way to do this is to configure NGINX to run as
the mytardis user, by changing the following in /etc/nginx/nginx.conf:

  # user www-data;
  user mytardis

and restarting the NGINX service.

When changing the NGINX user, you also need to delete or change ownership
of files in NGINX's proxy_temp_path (usually /var/lib/nginx/proxy/).

The NGINX location configuration for proxied downloads could look like this:

  location /protected/ {
    internal;
    alias /srv/;
  }

which corresponds to the following PROXY_DOWNLOAD_PREFIXES setting:

  PROXY_DOWNLOAD_PREFIXES = {
      '/srv/': '/protected/'
  }
"""

RECALL_URI_TEMPLATES = {}
"""
When a file recall (from tape/archive) is requested, MyTardis can
direct the request to an API endpoint provided by the tardis.apps.hsm
app, or to another API endpoint which can take a DataFileObject ID
and trigger a recall for the corresponding file on the HSM
(Hierarchical Storage Management) system.

For example,

  RECALL_URI_TEMPLATES = {
      'tardis.apps.hsm.storage.HsmFileSystemStorage':
      '/api/v1/hsm_replica/{dfo_id}/recall/'
  }
"""
