import djcelery
from datetime import timedelta
from os import path

# MUST change this to False for any serious use.
DEBUG = True

TEMPLATE_DEBUG = DEBUG

ADMINS = (('bob', 'bob@bobmail.com'), )

MANAGERS = ADMINS

# Dictionary containing the settings for all databases to be used.
# The DATABASES setting must configure a default database;
# any number of additional databases may also be specified.
DATABASES = {
    'default': {
        # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.sqlite3',
        # Name of the database to use. For SQLite, it's the full path.
        'NAME': 'db.sqlite3',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Fix 'SQLite backend does not support timezone-aware datetimes
# when USE_TZ is False.' error by setting USE_TZ to True

# Celery queue
BROKER_URL = 'django://'
'''
use django:, add kombu.transport.django to INSTALLED_APPS
or use redis: install redis separately and add the following to a
custom buildout.cfg:
    django-celery-with-redis
    redis
    hiredis
'''
# BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# A dictionary containing the settings for all caches to be used with
# Django. The CACHES setting must configure a default cache; any
# number of additional caches may also be specified.  Once the cache
# is set up, you'll need to add
# 'django.middleware.cache.UpdateCacheMiddleware' and
# 'django.middleware.cache.FetchFromCacheMiddleware'
# to your MIDDLEWARE_CLASSES setting below

# The MemcachedCache backend is required for the publication form app

# CACHES = {
#    'default': {
#        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#        'LOCATION': '127.0.0.1:11211',
#    }
# }

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.

TIME_ZONE = 'Australia/Melbourne'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html

LANGUAGE_CODE = 'en-us'

# Date format to use by default. ("jS F Y" => "8th March 2012")
# https://docs.djangoproject.com/en/1.3/ref/templates/builtins/#std:templatefilter-date  # noqa

DATE_FORMAT = "jS F Y"
DATETIME_FORMAT = "jS F Y H:i"

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.

USE_I18N = True

# SECRET_KEY has been removed. Generate one by referring to build.sh

ALLOWED_HOSTS = ['*']
'''
For security reasons this needs to be set to your hostname and/or IP
address in production.
'''

SITE_TITLE = None
'''
customise the title of your site
'''

SPONSORED_TEXT = None
'''
add text to the footer to acknowledge someone
'''

# once the cache is set up, you'll need to add
# 'django.middleware.cache.UpdateCacheMiddleware' and
# 'django.middleware.cache.FetchFromCacheMiddleware'
MIDDLEWARE_CLASSES = (
    # 'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.cache.FetchFromCacheMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tardis.tardis_portal.logging_middleware.LoggingMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'tardis.tardis_portal.auth.token_auth.TokenAuthMiddleware',
)

ROOT_URLCONF = 'tardis.urls'

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'tardis.tardis_portal.context_processors.global_contexts',
    'tardis.tardis_portal.context_processors.single_search_processor',
    'tardis.tardis_portal.context_processors.tokenuser_processor',
    'tardis.tardis_portal.context_processors.registration_processor',
    'tardis.tardis_portal.context_processors.user_details_processor',
]

TEMPLATE_LOADERS = (
    'tardis.template.loaders.app_specific.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.filesystem.Loader',
)


# Put strings here, like "/home/html/django_templates" or
# "C:/www/django/templates". Always use forward slashes, even on Windows.
# Don't forget to use absolute paths, not relative paths.
TEMPLATE_DIRS = (
    path.join(path.dirname(__file__),
              'tardis_portal/templates/').replace('\\', '/'),
)

STATIC_DOC_ROOT = path.join(path.dirname(__file__),
                            'tardis_portal/site_media').replace('\\', '/')


def get_admin_media_path():
    import pkgutil
    package = pkgutil.get_loader("django.contrib.admin")
    return path.join(package.filename, 'static', 'admin')

ADMIN_MEDIA_STATIC_DOC_ROOT = get_admin_media_path()

# FILE_STORE_PATH = path.abspath(path.join(path.dirname(__file__),
#     '../var/store/')).replace('\\', '/')
STAGING_PATH = path.abspath(path.join(path.dirname(__file__),
                                      '../var/staging/')).replace('\\', '/')
# SYNC_TEMP_PATH = path.abspath(path.join(path.dirname(__file__),
#     '../var/sync/')).replace('\\', '/')

DEFAULT_STORAGE_BASE_DIR = path.abspath(path.join(path.dirname(__file__),
                                        '../var/store/')).replace('\\', '/')

# LEGACY, ignore
FILE_STORE_PATH = DEFAULT_STORAGE_BASE_DIR
INITIAL_LOCATIONS = {}

METADATA_STORE_PATH = DEFAULT_STORAGE_BASE_DIR
'''
storage path for image paths stored in parameters. Better to set to another
location if possible
'''

STAGING_PROTOCOL = 'ldap'
STAGING_MOUNT_PREFIX = 'smb://localhost/staging/'
STAGING_MOUNT_USER_SUFFIX_ENABLE = False

REQUIRE_DATAFILE_CHECKSUMS = True
REQUIRE_DATAFILE_SIZES = True
REQUIRE_VALIDATION_ON_INGESTION = True

DEFAULT_FILE_STORAGE = \
    'tardis.tardis_portal.storage.MyTardisLocalFileSystemStorage'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = DEFAULT_STORAGE_BASE_DIR

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = None

# Static content location
STATIC_URL = '/static/'

# Used by "django collectstatic"
STATIC_ROOT = path.abspath(path.join(path.dirname(__file__), '..', 'static'))

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
# ADMIN_MEDIA_PREFIX = STATIC_URL + '/admin/'

STATICFILES_DIRS = (
    ('admin', ADMIN_MEDIA_STATIC_DOC_ROOT),
)

# Use cachable copies of static files
STATICFILES_STORAGE = \
    'django.contrib.staticfiles.storage.CachedStaticFilesStorage'

# A tuple of strings designating all applications that are enabled in
# this Django installation.
TARDIS_APP_ROOT = 'tardis.apps'
INSTALLED_APPS = (
    'django_extensions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',
    'tardis.template.loaders',
    'tardis.tardis_portal',
    'tardis.tardis_portal.templatetags',
    'registration',
    'south',
    'django_jasmine',
    'djcelery',
    'kombu.transport.django',
    'bootstrapform',
    'mustachejs',
    'tastypie',
    # these optional apps, may require extra settings
    'tardis.apps.publication_forms',
    'tardis.apps.oaipmh',
)

JASMINE_TEST_DIRECTORY = path.abspath(path.join(path.dirname(__file__),
                                                'tardis_portal',
                                                'tests',
                                                'jasmine'))


USER_PROVIDERS = (
    'tardis.tardis_portal.auth.localdb_auth.DjangoUserProvider',
)

GROUP_PROVIDERS = (
    'tardis.tardis_portal.auth.localdb_auth.DjangoGroupProvider',
    'tardis.tardis_portal.auth.token_auth.TokenGroupProvider',
)

# AUTH_PROVIDERS entry format:
# ('name', 'display name', 'backend implementation')
#   name - used as the key for the entry
#   display name - used as the displayed value in the login form
#   backend implementation points to the actual backend implementation
# We will assume that localdb will always be a default AUTH_PROVIDERS entry

AUTH_PROVIDERS = (
    ('localdb', 'Local DB',
     'tardis.tardis_portal.auth.localdb_auth.DjangoAuthBackend'),
)

# default authentication module for experiment ownership user during
# ingestion? Must be one of the above authentication provider names
DEFAULT_AUTH = 'localdb'

AUTH_PROFILE_MODULE = 'tardis_portal.UserProfile'

# New users are added to these groups by default.
NEW_USER_INITIAL_GROUPS = []

ACCOUNT_ACTIVATION_DAYS = 3

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'tardis.tardis_portal.auth.authorisation.ACLAwareBackend',
)

# Email Configuration

EMAIL_PORT = 587

EMAIL_HOST = 'smtp.gmail.com'

EMAIL_HOST_USER = 'bob@bobmail.com'

EMAIL_HOST_PASSWORD = 'bob'

EMAIL_USE_TLS = True

# Post Save Filters
# POST_SAVE_FILTERS = [
#    ("tardis.tardis_portal.filters.exif.make_filter",
#     ["EXIF", "http://exif.schema"]),  # this filter requires pyexiv2
#                                       # http://tilloy.net/dev/pyexiv2/
#    ]

# Post Save Filters
# POST_SAVE_FILTERS = [
#    ("tardis.tardis_portal.filters.diffractionimage.make_filter",
#     ["DIFFRACTION", "http://www.tardis.edu.au/schemas/trdDatafile/1",
#      "/Users/steve/Desktop/diffdump"]),  #  requires ccp4 diffdump binary
#    ]

# logging levels are: DEBUG, INFO, WARN, ERROR, CRITICAL
SYSTEM_LOG_LEVEL = 'INFO'
MODULE_LOG_LEVEL = 'INFO'

SYSTEM_LOG_FILENAME = 'request.log'
MODULE_LOG_FILENAME = 'tardis.log'

# Rollover occurs whenever the current log file is nearly maxBytes in length;
# if maxBytes is zero, rollover never occurs
SYSTEM_LOG_MAXBYTES = 0
MODULE_LOG_MAXBYTES = 0

# Uploadify root folder path, relative to STATIC root
UPLOADIFY_PATH = '%s/%s' % (STATIC_URL, 'js/lib/uploadify')

# Upload path that files are sent to
UPLOADIFY_UPLOAD_PATH = '%s/%s' % (MEDIA_URL, 'uploads')

# Download size limit: zero means no limit
DOWNLOAD_ARCHIVE_SIZE_LIMIT = 0

# temporary download file location
from tempfile import gettempdir
DOWNLOAD_TEMP_DIR = gettempdir()

# Safety margin for temporary space when downloading.  (Estimated archive
# file size + safety_margin must be less that available disk space ...)
DOWNLOAD_SPACE_SAFETY_MARGIN = 8388608

# Disable registration (copy to your settings.py first!)
# INSTALLED_APPS = filter(lambda x: x != 'registration', INSTALLED_APPS)

# Settings for the single search box
# Set HAYSTACK_SOLR_URL to the location of the SOLR server instance
SINGLE_SEARCH_ENABLED = False
HAYSTACK_SITECONF = 'tardis.search_sites'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = 'http://127.0.0.1:8080/solr'
if SINGLE_SEARCH_ENABLED:
    INSTALLED_APPS = INSTALLED_APPS + ('haystack',)
else:
    HAYSTACK_ENABLE_REGISTRATIONS = False

DEFAULT_INSTITUTION = "Monash University"

TOKEN_EXPIRY_DAYS = 30
TOKEN_LENGTH = 30
TOKEN_USERNAME = 'tokenuser'

REQUIRE_VALID_PUBLIC_CONTACTS = True

# RIF-CS Settings
OAI_DOCS_PATH = path.abspath(path.join(path.dirname(__file__), '../var/oai'))
RIFCS_PROVIDERS = (
    'tardis.tardis_portal.publish.provider.rifcsprovider.RifCsProvider',)
RIFCS_TEMPLATE_DIR = path.join(
    path.dirname(__file__),
    'tardis_portal/templates/tardis_portal/rif-cs/profiles/')
RIFCS_GROUP = "MyTARDIS Default Group"
RIFCS_KEY = "keydomain.example"
RELATED_INFO_SCHEMA_NAMESPACE = \
    'http://www.tardis.edu.au/schemas/related_info/2011/11/10'
RELATED_OTHER_INFO_SCHEMA_NAMESPACE = \
    'http://www.tardis.edu.au/schemas/experiment/annotation/2011/07/07'

DOI_ENABLE = False
DOI_XML_PROVIDER = 'tardis.tardis_portal.ands_doi.DOIXMLProvider'
# DOI_TEMPLATE_DIR = path.join(
#    TARDIS_DIR, 'tardis_portal/templates/tardis_portal/doi/')
DOI_TEMPLATE_DIR = path.join('tardis_portal/doi/')
DOI_APP_ID = ''
DOI_NAMESPACE = 'http://www.tardis.edu.au/schemas/doi/2011/12/07'
DOI_MINT_URL = 'https://services.ands.org.au/home/dois/doi_mint.php'
DOI_RELATED_INFO_ENABLE = False
DOI_BASE_URL = 'http://mytardis.example.com'

OAIPMH_PROVIDERS = [
    'tardis.apps.oaipmh.provider.experiment.DcExperimentProvider',
    'tardis.apps.oaipmh.provider.experiment.RifCsExperimentProvider',
]

REDIS_VERIFY_MANAGER = False
'''
Uses REDIS to keep track of files that fail to verify
'''
REDIS_VERIFY_MANAGER_SETUP = {
    'host': 'localhost',
    'port': 6379,
    'db': 1,
}

REDIS_VERIFY_DELAY = 86400  # 1 day = 86400
'''
delay between verification attempts in seconds
'''

CELERYBEAT_SCHEDULE = {
    "verify-files": {
        "task": "tardis_portal.verify_dfos",
        "schedule": timedelta(seconds=300)
    },
    # enable this task for the publication workflow
    # "update-publication-records": {
    #     "task": "apps.publication_forms.update_publication_records",
    #     "schedule": timedelta(seconds=300)
    # },
}

djcelery.setup_loader()

# DEFAULT_LOCATION = "local"

# INITIAL_LOCATIONS = [{'name': DEFAULT_LOCATION,
#                       'url': 'file://' + FILE_STORE_PATH,
#                       'provider': 'local',
#                       'type': 'online',
#                       'priority': 10},
# #                     {'name': 'sync',
# #                      'url': 'file://' + SYNC_PATH,
# #                      'provider': 'local',
# #                      'type': 'external',
# #                      'priority': 8},
#                      {'name': 'staging',
#                       'provider': 'local',
#                       'url': 'file://' + STAGING_PATH,
#                       'type': 'external',
#                       'priority': 5}]

DEFAULT_MIGRATION_DESTINATION = 'unknown'

TRANSFER_PROVIDERS = {
    'http': 'tardis.tardis_portal.transfer.SimpleHttpTransfer',
    'dav': 'tardis.tardis_portal.transfer.WebDAVTransfer',
    'local': 'tardis.tardis_portal.transfer.LocalTransfer'}

UPLOAD_METHOD = False
'''
Old version: UPLOAD_METHOD = "uploadify".
This can be changed to an app that provides an upload_button function,
eg. "tardis.apps.filepicker.views.upload_button" to use a fancy
commercial uploader.
To use filepicker, please also get an API key at http://filepicker.io
'''
# FILEPICKER_API_KEY = "YOUR KEY"

ARCHIVE_FILE_MAPPERS = {
    'deep-storage': (
        'tardis.apps.deep_storage_download_mapper.mapper.deep_storage_mapper',
    ),
}

# Site's default archive organization (i.e. path structure)
DEFAULT_ARCHIVE_ORGANIZATION = 'deep-storage'

DEFAULT_ARCHIVE_FORMATS = ['tar']
'''
Site's preferred archive types, with the most preferred first
other available option: 'tgz'. Add to list if desired
'''

# DEEP_DATASET_STORAGE = True
# '''
# Set to true if you want to preserve folder structure on "stage_file" ingest,
# eg. via the METS importer.
# Currently, only tested for the METS importer.
# '''


# Get version from git to be displayed on About page.
def get_git_version():
    repo_dir = path.dirname(path.dirname(path.abspath(__file__)))

    def run_git(args):
        import subprocess
        process = subprocess.Popen('git %s' % args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True,
                                   cwd=repo_dir,
                                   universal_newlines=True)
        return process.communicate()[0]

    try:
        info = {
            'commit_id': run_git("log -1 --format='%H'").strip(),
            'date': run_git("log -1 --format='%cd' --date=rfc").strip(),
            'branch': run_git("rev-parse --abbrev-ref HEAD").strip(),
            'tag': run_git("describe --abbrev=0 --tags").strip(),
        }
    except Exception:
        return ["unavailable"]
    return info

MYTARDIS_VERSION = get_git_version()
# If you want enable user agent sensing, copy this to settings.py
# and uncomment it.
#
# USER_AGENT_SENSING = True
# if USER_AGENT_SENSING:
#    from os import environ
#    # Workaround for bug in ua_parser ... can't find its builtin copy
#    # of regexes.yaml ... in versions 0.3.2 and earlier.  Remove when fixed.
#    environ['UA_PARSER_YAML'] = '/opt/mytardis/current/ua_parser_regexes.yaml'
#
#    INSTALLED_APPS = INSTALLED_APPS + ('django_user_agents',)
#    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + \
#        ('django_user_agents.middleware.UserAgentMiddleware',)

AUTOGENERATE_API_KEY = False
'''
Generate a tastypie API key with user post_save
(tardis/tardis_portal/models/hooks.py)
'''

BLEACH_ALLOWED_TAGS = [
    'a',
    'abbr',
    'acronym',
    'b',
    'blockquote',
    'code',
    'em',
    'i',
    'li',
    'ol',
    'strong',
    'ul',
]
'''
These are the default bleach values and shown here as an example.
'''

BLEACH_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'abbr': ['title'],
    'acronym': ['title'],
}
'''
These are the default bleach values and shown here as an example.
'''

SFTP_PORT = 2200
SFTP_GEVENT = False
SFTP_HOST_KEY = (
    "-----BEGIN RSA PRIVATE KEY-----\n"
    "MIICXgIBAAKCAIEAl7sAF0x2O/HwLhG68b1uG8KHSOTqe3Cdlj5i/1RhO7E2BJ4B\n"
    "3jhKYDYtupRnMFbpu7fb21A24w3Y3W5gXzywBxR6dP2HgiSDVecoDg2uSYPjnlDk\n"
    "HrRuviSBG3XpJ/awn1DObxRIvJP4/sCqcMY8Ro/3qfmid5WmMpdCZ3EBeC0CAwEA\n"
    "AQKCAIBSGefUs5UOnr190C49/GiGMN6PPP78SFWdJKjgzEHI0P0PxofwPLlSEj7w\n"
    "RLkJWR4kazpWE7N/bNC6EK2pGueMN9Ag2GxdIRC5r1y8pdYbAkuFFwq9Tqa6j5B0\n"
    "GkkwEhrcFNBGx8UfzHESXe/uE16F+e8l6xBMcXLMJVo9Xjui6QJBAL9MsJEx93iO\n"
    "zwjoRpSNzWyZFhiHbcGJ0NahWzc3wASRU6L9M3JZ1VkabRuWwKNuEzEHNK8cLbRl\n"
    "TyH0mceWXcsCQQDLDEuWcOeoDteEpNhVJFkXJJfwZ4Rlxu42MDsQQ/paJCjt2ONU\n"
    "WBn/P6iYDTvxrt/8+CtLfYc+QQkrTnKn3cLnAkEAk3ixXR0h46Rj4j/9uSOfyyow\n"
    "qHQunlZ50hvNz8GAm4TU7v82m96449nFZtFObC69SLx/VsboTPsUh96idgRrBQJA\n"
    "QBfGeFt1VGAy+YTLYLzTfnGnoFQcv7+2i9ZXnn/Gs9N8M+/lekdBFYgzoKN0y4pG\n"
    "2+Q+Tlr2aNlAmrHtkT13+wJAJVgZATPI5X3UO0Wdf24f/w9+OY+QxKGl86tTQXzE\n"
    "4bwvYtUGufMIHiNeWP66i6fYCucXCMYtx6Xgu2hpdZZpFw==\n"
    "-----END RSA PRIVATE KEY-----\n")
'''
public, useless key, debugging use only
'''

# Show the Rapid Connect login button.
RAPID_CONNECT_ENABLED = False

RAPID_CONNECT_CONFIG = {}

RAPID_CONNECT_CONFIG['secret'] = 'CHANGE_ME'
RAPID_CONNECT_CONFIG['authnrequest_url'] = 'CHANGE_ME'
'''something like
'https://rapid.test.aaf.edu.au/jwt/authnrequest/research/XXXXXXXXXXXXXXXX'
'''

RAPID_CONNECT_CONFIG['iss'] = 'https://rapid.test.aaf.edu.au'
''' 'https://rapid.test.aaf.edu.au' or 'https://rapid.aaf.edu.au'
'''
RAPID_CONNECT_CONFIG['aud'] = 'https://example.com/rc/'
'''Public facing URL that accepts the HTTP/HTTPS POST request from
Rapid Connect.
'''


# Example settings for the publication form workflow. Also requires the
# corresponding app in 'INSTALLED_APPS' and the corresponding task to be
# enabled

# Publication form settings #
# PUBLICATION_NOTIFICATION_SENDER_EMAIL = 'emailsender@mytardisserver'

# PUBLICATION_OWNER_GROUP = 'publication-admin'

# PUBLICATION_SCHEMA_ROOT = 'http://www.tardis.edu.au/schemas/publication/'

# This schema holds bibliographic details including authors and
# acknowledgements
# PUBLICATION_DETAILS_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'details/'

# Any experiment with this schema is treated as a draft publication
# This schema will be created automatically if not present
# PUBLICATION_DRAFT_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'draft/'

# Form mappings
# PUBLICATION_FORM_MAPPINGS is a list of dictionaries that contain the
# following parameters:
# dataset_schema: the namespace of the schema that triggers the form to be used
# publication_schema: the namspace of the schema that should be added to the
# publication
# form_template: a URL to the form template (usually static HTML)
# PUBLICATION_FORM_MAPPINGS = [
#     {'dataset_schema': 'http://example.com/a_dataset_schema',
#      'publication_schema': 'http://example.com/a_publication_schema',
#      'form_template': '/static/publication-form/form-template.html'}]
# Note: dataset_schema is treated as a regular expression

# The PDB publication schema is used for any experiments that reference a
# PDB structure
# It is defined here as a setting because it is used both for the publication
# form and for fetching data from PDB.org and must always match.
# PDB_PUBLICATION_SCHEMA_ROOT = 'http://synchrotron.org.au/pub/mx/pdb/'
# PDB_SEQUENCE_PUBLICATION_SCHEMA = PDB_PUBLICATION_SCHEMA_ROOT+'sequence/'
# PDB_CITATION_PUBLICATION_SCHEMA = PDB_PUBLICATION_SCHEMA_ROOT+'citation/'
# PDB_REFRESH_INTERVAL = timedelta(days=7)

# PUBLICATION_FORM_MAPPINGS = [
#     {'dataset_schema': r'^http://synchrotron.org.au/mx/',
#      'publication_schema': PDB_PUBLICATION_SCHEMA_ROOT,
#      'form_template': '/static/publication-form/mx-pdb-template.html'},
#     {'dataset_schema': r'^http://synchrotron.org.au/mx/',
#      'publication_schema': 'http://synchrotron.org.au/pub/mx/dataset/',
#      'form_template':
#      '/static/publication-form/mx-dataset-description-template.html'}]

# Put your API_ID for the Monash DOI minting service here. For other DOI
# minting, please contact the developers
# MODC_DOI_API_ID = ''
# MODC_DOI_API_PASSWORD = ''
# MODC_DOI_MINT_DEFINITION = 'https://doiserver/modc/ws/MintDoiService.wsdl'
# MODC_DOI_ACTIVATE_DEFINITION = 'https://doiserver/modc/ws/' \
#     'ActivateDoiService.wsdl'
# MODC_DOI_DEACTIVATE_DEFINITION = 'https://doiserver/modc/ws/' \
#     'DeactivateDoiService.wsdl'
# MODC_DOI_ENDPOINT = 'https://doiserver/modc/ws/'
# MODC_DOI_MINT_URL_ROOT = 'http://mytardisserver/'
