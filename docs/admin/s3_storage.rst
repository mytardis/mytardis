S3 compatible storage
=====================

S3 and S3 compatible storage backends are supported by the django-storages package.

We added some modifications that allow database driven configuration. Until these
changes are accepted by the maintainer, use this fork and branch:
https://github.com/monash-merc/django-storages/tree/mytardis-branch

Install it with::

   pip install -e git+https://github.com/monash-merc/django-storages.git@mytardis-branch#egg=django-storages

Configuration
-------------

The following options can be set as StorageBoxOption on your S3 storage box or
system wide in your Django settings (a default of * labels mandatory settings):

================== ============================================== ============================
StorageBoxOption   Django Setting                                 Default
------------------ ---------------------------------------------- ----------------------------
access_key         AWS_S3_ACCESS_KEY_ID AWS_ACCESS_KEY_ID         \*
secret_key         AWS_S3_SECRET_ACCESS_KEY AWS_SECRET_ACCESS_KEY \*
file_overwrite     AWS_S3_FILE_OVERWRITE                          True
headers            AWS_HEADERS                                    ``{}``
bucket_name        AWS_STORAGE_BUCKET_NAME                        \*
auto_create_bucket AWS_AUTO_CREATE_BUCKET                         False
default_acl        AWS_DEFAULT_ACL                                ``public-read``
bucket_acl         AWS_BUCKET_ACL                                 ``default_acl``
querystring_auth   AWS_QUERYSTRING_AUTH                           True
querystring_expire AWS_QUERYSTRING_EXPIRE                         3600
reduced_redundancy AWS_REDUCED_REDUNDANCY                         False
location           AWS_LOCATION                                   ``''``
encryption         AWS_S3_ENCRYPTION                              False
custom_domain      AWS_S3_CUSTOM_DOMAIN                           None
calling_format     AWS_S3_CALLING_FORMAT                          ``SubdomainCallingFormat()``
secure_urls        AWS_S3_SECURE_URLS                             True
file_name_charset  AWS_S3_FILE_NAME_CHARSET                       ``utf-8``
gzip               AWS_IS_GZIPPED                                 False
preload_metadata   AWS_PRELOAD_METADATA                           False
gzip_content_types GZIP_CONTENT_TYPES                             ``('text/css', 'text/javascript', 'application/javascript', 'application/x-javascript', 'image/svg+xml')``
url_protocol       AWS_S3_URL_PROTOCOL                            ``http:``
host               AWS_S3_HOST                                    ``S3Connection.DefaultHost``
use_ssl            AWS_S3_USE_SSL                                 True
port               AWS_S3_PORT                                    None
proxy              AWS_S3_PROXY_HOST                              None
proxy_port         AWS_S3_PROXY_PORT                              None
------------------ ---------------------------------------------- ----------------------------
The max amount of memory a returned file can take up before being rolled over into a temporary file on disk. Default is 0: Do not roll over.
----------------------------------------------------------------------------------------------
max_memory_size    AWS_S3_MAX_MEMORY_SIZE                         0
================== ============================================== ============================
