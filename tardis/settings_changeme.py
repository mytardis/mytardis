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
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        # Name of the database to use. For SQLite, it's the full path.
        'NAME': 'tardis',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

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
    'tardis.tardis_portal.logging_middleware.LoggingMiddleware',
    'tardis.tardis_portal.auth.AuthorizationMiddleware',
    'django.middleware.transaction.TransactionMiddleware')

ROOT_URLCONF = 'tardis.urls'

TEMPLATE_CONTEXT_PROCESSORS = ('django.core.context_processors.request',
                               'django.contrib.auth.context_processors.auth',
                               'django.core.context_processors.debug',
                               'django.core.context_processors.i18n',
                                'tardis.tardis_portal.context_processors.single_search_processor',
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

ADMIN_MEDIA_STATIC_DOC_ROOT = path.join(path.dirname(__file__),
    '../parts/django/django/contrib/admin/media/').replace('\\', '/')

FILE_STORE_PATH = path.abspath(path.join(path.dirname(__file__),
    '../var/store/')).replace('\\', '/')
STAGING_PATH = path.abspath(path.join(path.dirname(__file__),
    '../var/staging/')).replace('\\', '/')
STAGING_PROTOCOL = 'ldap'
STAGING_MOUNT_PREFIX = 'smb://localhost/staging/'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"

MEDIA_ROOT = STATIC_DOC_ROOT

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"

MEDIA_URL = '/site_media/'

#set to empty tuple () for no apps
#TARDIS_APPS = ('mrtardis', )
TARDIS_APPS = ()
TARDIS_APP_ROOT = 'tardis.apps'

if TARDIS_APPS:
    apps = tuple(["%s.%s" % (TARDIS_APP_ROOT, app) for app in TARDIS_APPS])
else:
    apps = ()

# A tuple of strings designating all applications that are enabled in
# this Django installation.

INSTALLED_APPS = (
    'django_extensions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'tardis.tardis_portal',
    'tardis.tardis_portal.templatetags',
    'registration',
    'south',
    'haystack',
    ) + apps

USER_PROVIDERS = ('tardis.tardis_portal.auth.localdb_auth.DjangoUserProvider',
)

GROUP_PROVIDERS = ('tardis.tardis_portal.auth.localdb_auth.DjangoGroupProvider',
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

# logging levels are: DEBUG, INFO, WARN, ERROR, CRITICAL
SYSTEM_LOG_LEVEL = 'INFO'
MODULE_LOG_LEVEL = 'INFO'

SYSTEM_LOG_FILENAME = 'request.log'
MODULE_LOG_FILENAME = 'tardis.log'

# Rollover occurs whenever the current log file is nearly maxBytes in length;
# if maxBytes is zero, rollover never occurs
SYSTEM_LOG_MAXBYTES = 0
MODULE_LOG_MAXBYTES = 0

# Uploadify root folder path, relative to MEDIA_ROOT
UPLOADIFY_PATH = '%s%s' % (MEDIA_URL, 'js/uploadify/')

# Upload path that files are sent to
UPLOADIFY_UPLOAD_PATH = '%s%s' % (MEDIA_URL, 'uploads/')

# Settings for the single search box
# Set HAYSTACK_SOLR_URL to the location of the SOLR server instance
SINGLE_SEARCH_ENABLED = False 
HAYSTACK_SITECONF = 'tardis.search_sites'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = 'http://127.0.0.1:8080/solr'
if not SINGLE_SEARCH_ENABLED:
    HAYSTACK_ENABLE_REGISTRATIONS = False

DEFAULT_INSTITUTION = "Monash University"

#Are the datasets ingested via METS xml (web services) to be immutable?
IMMUTABLE_METS_DATASETS = True
