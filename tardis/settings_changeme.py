import djcelery
from datetime import timedelta
from os import path

DEBUG = False

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
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Celery queue uses Django for persistence
BROKER_TRANSPORT = 'django'

# A dictionary containing the settings for all caches to be used with
# Django. The CACHES setting must configure a default cache; any
# number of additional caches may also be specified.  Once the cache
# is set up, you'll need to add
# 'django.middleware.cache.UpdateCacheMiddleware' and
# 'django.middleware.cache.FetchFromCacheMiddleware'
# to your MIDDLEWARE_CLASSES setting below

#CACHES = {
#    'default': {
#        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#        'LOCATION': '127.0.0.1:11211',
#    }
#}

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
# https://docs.djangoproject.com/en/1.3/ref/templates/builtins/#std:templatefilter-date

DATE_FORMAT = "jS F Y"
DATETIME_FORMAT = "jS F Y H:i"

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.

USE_I18N = True

# Make this unique, and don't share it with anybody.

SECRET_KEY = 'ij!%7-el^^rptw$b=iol%78okl10ee7zql-()z1r6e)gbxd3gl'

# once the cache is set up, you'll need to add
# 'django.middleware.cache.UpdateCacheMiddleware' and
# 'django.middleware.cache.FetchFromCacheMiddleware'
MIDDLEWARE_CLASSES = (
    #'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tardis.tardis_portal.logging_middleware.LoggingMiddleware',
    'tardis.tardis_portal.auth.AuthorizationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'tardis.tardis_portal.auth.token_auth.TokenAuthMiddleware',
)

ROOT_URLCONF = 'tardis.urls'

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
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


# Temporarily disable transaction management until everyone agrees that
# we should start handling transactions
DISABLE_TRANSACTION_MANAGEMENT = False

STATIC_DOC_ROOT = path.join(path.dirname(__file__),
                               'tardis_portal/site_media').replace('\\', '/')

def get_admin_media_path():
    import pkgutil
    package = pkgutil.get_loader("django.contrib.admin")
    return path.join(package.filename, 'static', 'admin')

ADMIN_MEDIA_STATIC_DOC_ROOT = get_admin_media_path()

FILE_STORE_PATH = path.abspath(path.join(path.dirname(__file__),
    '../var/store/')).replace('\\', '/')
STAGING_PATH = path.abspath(path.join(path.dirname(__file__),
    '../var/staging/')).replace('\\', '/')
SYNC_TEMP_PATH = path.abspath(path.join(path.dirname(__file__),
    '../var/sync/')).replace('\\', '/')

STAGING_PROTOCOL = 'ldap'
STAGING_MOUNT_PREFIX = 'smb://localhost/staging/'
STAGING_MOUNT_USER_SUFFIX_ENABLE = False

REQUIRE_DATAFILE_CHECKSUMS = True
REQUIRE_DATAFILE_SIZES = True
REQUIRE_VALIDATION_ON_INGESTION = True

DEFAULT_FILE_STORAGE = 'tardis.tardis_portal.storage.MyTardisLocalFileSystemStorage'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = FILE_STORE_PATH

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = None

# Static content location
STATIC_URL = '/static/'

# Used by "django collectstatic"
STATIC_ROOT = path.abspath(path.join(path.dirname(__file__),'..','static'))

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
# ADMIN_MEDIA_PREFIX = STATIC_URL + '/admin/'

STATICFILES_DIRS = (
    ('admin', ADMIN_MEDIA_STATIC_DOC_ROOT),
)

# Use cachable copies of static files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.CachedStaticFilesStorage'

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
#POST_SAVE_FILTERS = [
#    ("tardis.tardis_portal.filters.exif.make_filter",
#     ["EXIF", "http://exif.schema"]),  # this filter requires pyexiv2
#                                       # http://tilloy.net/dev/pyexiv2/
#    ]

# Post Save Filters
#POST_SAVE_FILTERS = [
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

#Are the datasets ingested via METS xml (web services) to be immutable?
IMMUTABLE_METS_DATASETS = True

TOKEN_EXPIRY_DAYS = 30
TOKEN_LENGTH = 30
TOKEN_USERNAME = 'tokenuser'

REQUIRE_VALID_PUBLIC_CONTACTS = True

# RIF-CS Settings
OAI_DOCS_PATH = path.abspath(path.join(path.dirname(__file__), '../var/oai'))
RIFCS_PROVIDERS = ('tardis.tardis_portal.publish.provider.rifcsprovider.RifCsProvider',)
RIFCS_TEMPLATE_DIR = path.join(path.dirname(__file__),
    'tardis_portal/templates/tardis_portal/rif-cs/profiles/')
RIFCS_GROUP = "MyTARDIS Default Group"
RIFCS_KEY = "keydomain.example"
RELATED_INFO_SCHEMA_NAMESPACE = 'http://www.tardis.edu.au/schemas/related_info/2011/11/10'
RELATED_OTHER_INFO_SCHEMA_NAMESPACE = 'http://www.tardis.edu.au/schemas/experiment/annotation/2011/07/07'

DOI_ENABLE = False
DOI_XML_PROVIDER = 'tardis.tardis_portal.ands_doi.DOIXMLProvider'
#DOI_TEMPLATE_DIR = path.join(TARDIS_DIR, 'tardis_portal/templates/tardis_portal/doi/')
DOI_TEMPLATE_DIR = path.join('tardis_portal/doi/')
DOI_APP_ID = ''
DOI_NAMESPACE = 'http://www.tardis.edu.au/schemas/doi/2011/12/07'
DOI_MINT_URL = 'https://services.ands.org.au/home/dois/doi_mint.php'
DOI_RELATED_INFO_ENABLE = False
DOI_BASE_URL='http://mytardis.example.com'

OAIPMH_PROVIDERS = [
    'tardis.apps.oaipmh.provider.experiment.DcExperimentProvider',
    'tardis.apps.oaipmh.provider.experiment.RifCsExperimentProvider',
]


CELERYBEAT_SCHEDULE = {
      "verify-files": {
        "task": "tardis_portal.verify_files",
        "schedule": timedelta(seconds=30)
      },
    }

djcelery.setup_loader()

DEFAULT_LOCATION = "local"

INITIAL_LOCATIONS = [{'name': DEFAULT_LOCATION,
                      'url': 'file://' + FILE_STORE_PATH,
                      'provider': 'local',
                      'type': 'online',
                      'priority': 10},
#                     {'name': 'sync',
#                      'url': 'file://' + SYNC_PATH,
#                      'provider': 'local',
#                      'type': 'external',
#                      'priority': 8},
                     {'name': 'staging',
                      'provider': 'local',
                      'url': 'file://' + STAGING_PATH,
                      'type': 'external',
                      'priority': 5}]

DEFAULT_MIGRATION_DESTINATION = 'unknown'

TRANSFER_PROVIDERS = {
    'http': 'tardis.tardis_portal.transfer.SimpleHttpTransfer',
    'dav': 'tardis.tardis_portal.transfer.WebDAVTransfer',
    'local': 'tardis.tardis_portal.transfer.LocalTransfer'}

UPLOAD_METHOD = "uploadify"
'''
can be changed to an app that provides an upload_button function,
eg. "tardis.apps.filepicker.views.upload_button" to use a fancy
commercial uploader.
To use filepicker, please also get an API key at http://filepicker.io
'''
#FILEPICKER_API_KEY = "YOUR KEY"

ARCHIVE_FILE_MAPPERS = {
#    'test': ('tardis.apps.example.ExampleMapper',),
#    'test2': ('tardis.apps.example.ExampleMapper', {'foo': 1})
    }

# Site's default archive organization (i.e. path structure)
DEFAULT_ARCHIVE_ORGANIZATION = 'classic'

# Site's preferred archive types, with the most preferred first
DEFAULT_ARCHIVE_FORMATS = ['zip', 'tar']

# If you want enable user agent sensing, copy this to settings.py
# and uncomment it.
#
#USER_AGENT_SENSING = True
#if USER_AGENT_SENSING:
#    from os import environ
#    # Workaround for bug in ua_parser ... can't find its builtin copy
#    # of regexes.yaml ... in versions 0.3.2 and earlier.  Remove when fixed.
#    environ['UA_PARSER_YAML'] = '/opt/mytardis/current/ua_parser_regexes.yaml'
#
#    INSTALLED_APPS = INSTALLED_APPS + ('django_user_agents',)
#    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + \
#        ('django_user_agents.middleware.UserAgentMiddleware',)
