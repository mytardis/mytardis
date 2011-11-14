from os import path
import logging

# settings_global will be imported by settings_pre

DEBUG = True
TEMPLATE_DEBUG = DEBUG

#
# settings_core can safely define the following variables:
#
#    PROJ_DIR
#    TARDIS_DIR
#    LOCAL_APPS            # Used to list additional applications to install
#    TARDIS_APPS
#    SINGLE_SEARCH_ENABLED
#
# and must define:
#
#    DATABASES
#
PROJ_DIR = path.abspath(path.dirname(__file__))
TARDIS_DIR = PROJ_DIR
TARDIS_APPS = ()
LOCAL_APPS = ()
SINGLE_SEARCH_ENABLED = False 
try:
    from settings_core import *
except:
    pass

# logging levels are: DEBUG, INFO, WARN, ERROR, CRITICAL
#MODULE_LOG_LEVEL = logging.DEBUG
#MODULE_LOG_FILENAME = 'tardis.log'
#MODULE_LOG_MAXBYTES = 0

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
            },
        },
    'filters': {
        },
    'handlers': {
        'root-handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': 'root.log',
            'maxBytes': 10000000,
            'backupCount': 5
            },
        'rotate': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': 'logging.log',
            'maxBytes': 10000000,
            'backupCount': 5
            },
        'request-handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': 'request.log',
            'maxBytes': 10000000,
            'backupCount': 5
            },
        },
    'loggers': {
        '' : {
            'handlers': ['root-handler'],
            'propagate' : True,
            'level': 'DEBUG'
            },
        'django' : {
            'handlers': ['rotate'],
            'propagate' : True,
            'level': 'DEBUG'
            },
        'django.request' : {
            'handlers': ['request-handler'],
            'propagate' : True,
            'level': 'WARN'
            }
        }
}


ADMINS = (('bob', 'bob@bobmail.com'), )

MANAGERS = ADMINS

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

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.

USE_I18N = True

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".

ADMIN_MEDIA_PREFIX = '/media/'

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
    'tardis.tardis_portal.minidetector.Middleware',
    #'tardis.tardis_portal.logging_middleware.LoggingMiddleware',
    'tardis.tardis_portal.auth.AuthorizationMiddleware',
    'django.middleware.transaction.TransactionMiddleware')

ROOT_URLCONF = 'tardis.urls'

context_processors = ['django.core.context_processors.request',
       'django.contrib.auth.context_processors.auth',
       'django.core.context_processors.debug',
       'django.core.context_processors.i18n',
        'tardis.tardis_portal.context_processors.tokenuser_processor',
        ]

if SINGLE_SEARCH_ENABLED:
    context_processors.append('tardis.tardis_portal.single_search_processors.single_search_processor')
TEMPLATE_CONTEXT_PROCESSORS = tuple(context_processors)

# Put strings here, like "/home/html/django_templates" or
# "C:/www/django/templates". Always use forward slashes, even on Windows.
# Don't forget to use absolute paths, not relative paths.
TEMPLATE_DIRS = (
    path.join(TARDIS_DIR, 'tardis_portal/templates/').replace('\\', '/'),
)

# Temporarily disable transaction management until everyone agrees that
# we should start handling transactions
DISABLE_TRANSACTION_MANAGEMENT = False

STATIC_DOC_ROOT = path.join(TARDIS_DIR, 'tardis_portal/site_media')

ADMIN_MEDIA_STATIC_DOC_ROOT = path.join(PROJ_DIR,
    'parts/django/django/contrib/admin/media/')

FILE_STORE_PATH = path.abspath(path.join(PROJ_DIR, 'var/store/'))
STAGING_PATH = path.abspath(path.join(PROJ_DIR, 'var/staging/'))
STAGING_PROTOCOL = 'ldap'
STAGING_MOUNT_PREFIX = 'smb://localhost/staging/'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"

MEDIA_ROOT = STATIC_DOC_ROOT

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"

MEDIA_URL = '/site_media/'

# A tuple of strings designating all applications that are enabled in
# this Django installation.
apps = [
    'django_extensions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'registration',
    'south',
    'tardis.tardis_portal',
    ]
apps.extend(LOCAL_APPS)
if SINGLE_SEARCH_ENABLED:
    apps.append('haystack')
# By default, no additional applications are installed.
# TARDIS_APPS should be over-written in settings_pre.py
TARDIS_APP_ROOT = 'tardis.apps'
if TARDIS_APPS:
    apps.extend(["%s.%s" % (TARDIS_APP_ROOT, app) for app in TARDIS_APPS])
INSTALLED_APPS = tuple(apps)

USER_PROVIDERS = ('tardis.tardis_portal.auth.localdb_auth.DjangoUserProvider',
)

GROUP_PROVIDERS = ('tardis.tardis_portal.auth.localdb_auth.DjangoGroupProvider',
                    'tardis.tardis_portal.auth.token_auth.TokenGroupProvider',
                   'tardis.tardis_portal.auth.ip_auth.IPGroupProvider'
)

# AUTH_PROVIDERS entry format:
# ('name', 'display name', 'backend implementation')
#   name - used as the key for the entry
#   display name - used as the displayed value in the login form
#   backend implementation points to the actual backend implementation
# We will assume that localdb will always be a default AUTH_PROVIDERS entry

AUTH_PROVIDERS = (
    ('localdb', 'Local DB', 'tardis.tardis_portal.auth.localdb_auth.DjangoAuthBackend'),
)

# default authentication module for experiment ownership user during
# ingestion? Must be one of the above authentication provider names
DEFAULT_AUTH = 'localdb'

AUTH_PROFILE_MODULE = 'tardis_portal.UserProfile'


ACCOUNT_ACTIVATION_DAYS = 3

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


# Uploadify root folder path, relative to MEDIA_ROOT
UPLOADIFY_PATH = '%s%s' % (MEDIA_URL, 'js/uploadify/')

# Upload path that files are sent to
UPLOADIFY_UPLOAD_PATH = '%s%s' % (MEDIA_URL, 'uploads/')

# django-debug-toolbar configuration
INTERNAL_IPS = ('127.0.0.1',)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}
DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    # Disabled because a bug in SUDS means this breaks VBL logins.
    #'debug_toolbar.panels.logger.LoggingPanel',
)


# Settings for the single search box
# Set HAYSTACK_SOLR_URL to the location of the SOLR server instance
if SINGLE_SEARCH_ENABLED:
    HAYSTACK_SITECONF = 'tardis.search_sites'
    HAYSTACK_SEARCH_ENGINE = 'solr'
    HAYSTACK_SOLR_URL = 'http://127.0.0.1:8080/solr'
    HAYSTACK_ENABLE_REGISTRATIONS = SINGLE_SEARCH_ENABLED

DEFAULT_INSTITUTION = "MyTARDIS Default Installation"

#Are the datasets ingested via METS xml (web services) to be immutable?
IMMUTABLE_METS_DATASETS = False

# Token Access Settings
TOKEN_EXPIRY_DAYS = 30
TOKEN_LENGTH = 30
TOKEN_USERNAME = 'tokenuser'

# RIF-CS Settings
OAI_DOCS_PATH = path.abspath(path.join(PROJ_DIR, 'var/oai'))
RIFCS_PROVIDERS = ('tardis.tardis_portal.publish.provider.RifCsProvider',)
RIFCS_TEMPLATE_DIR = path.join(TARDIS_DIR, 
    'tardis_portal/templates/tardis_portal/rif-cs/profiles/')
RIFCS_GROUP = "MyTARDIS Default Group"
RELATED_INFO_SCHEMA_NAMESPACE = 'http://www.tardis.edu.au/schemas/related_info/2011/11/10'
RELATED_OTHER_INFO_SCHEMA_NAMESPACE = 'http://www.tardis.edu.au/schemas/experiment/annotation/2011/07/07'


# Allow the local installation to override the defaults
try:
    from settings_custom import *
except:
    pass

