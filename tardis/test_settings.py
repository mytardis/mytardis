from os import path

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

DEBUG = False

DATABASES = {
    'default': {
        # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.sqlite3',
        # Name of the database to use. For SQLite, it's the full path.
        'NAME': ':memory:',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# default authentication module for experiment ownership user during
# ingestion? Must be one of the above authentication provider names
DEFAULT_AUTH = 'localdb'

#ROOT_URLCONF = 'tardis.urls'

FILE_STORE_PATH = path.abspath(path.join(path.dirname(__file__),
                                         '../var/store/'))
STAGING_PATH = path.abspath(path.join(path.dirname(__file__),
                                      "../var/staging/"))

STAGING_PROTOCOL = 'localdb'
STAGING_MOUNT_PREFIX = 'smb://localhost/staging/'

GET_FULL_STAGING_PATH_TEST = path.join(STAGING_PATH, "test_user")

SITE_ID = '1'

#TEMPLATE_DIRS = ['.']
# Put strings here, like "/home/html/django_templates" or
# "C:/www/django/templates". Always use forward slashes, even on Windows.
# Don't forget to use absolute paths, not relative paths.
TEMPLATE_DIRS = (
    path.join(path.dirname(__file__),
    'tardis_portal/templates/').replace('\\', '/'),
                 
  path.join(path.dirname(__file__),
    'apps/hpctardis/publish/').replace('\\', '/'),
                 
    path.join(path.dirname(__file__),
    'tardis_portal/publish/').replace('\\', '/'),                 
)


STATIC_DOC_ROOT = path.join(path.dirname(__file__),
                            'tardis_portal/site_media').replace('\\', '/')

MEDIA_ROOT = STATIC_DOC_ROOT

MEDIA_URL = '/site_media/'

ADMIN_MEDIA_STATIC_DOC_ROOT = path.join(path.dirname(__file__),
                                        '../parts/django/django/contrib/admin/media/').replace('\\', '/')

EMAIL_LINK_HOST = "http://127.0.0.1:8080"


AUTH_PROVIDERS = (('localdb', 'Local DB',
                  'tardis.tardis_portal.auth.localdb_auth.DjangoAuthBackend'),
                  ('vbl', 'VBL',
                   'tardis.tardis_portal.tests.mock_vbl_auth.MockBackend'),
                  ('ldap', 'LDAP',
                   'tardis.tardis_portal.auth.ldap_auth.ldap_auth'),
)
USER_PROVIDERS = ('tardis.tardis_portal.auth.localdb_auth.DjangoUserProvider',)

GROUP_PROVIDERS = ('tardis.tardis_portal.auth.localdb_auth.DjangoGroupProvider',
                   'tardis.tardis_portal.auth.ip_auth.IPGroupProvider'
)

DOWNLOAD_PROVIDERS = (
    ('vbl', 'tardis.tardis_portal.tests.mock_vbl_download'),
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tardis.tardis_portal.auth.AuthorizationMiddleware',
    'tardis.tardis_portal.logging_middleware.LoggingMiddleware',
    'tardis.tardis_portal.minidetector.Middleware',
    'django.middleware.transaction.TransactionMiddleware',
      'tardis.tardis_portal.filters.FilterInitMiddleware'
)

TARDIS_APP_ROOT = 'tardis.apps'
TARDIS_APPS = ('equipment',)

if TARDIS_APPS:
    apps = tuple(["%s.%s" % (TARDIS_APP_ROOT, app) for app in TARDIS_APPS])
else:
    apps = ()

INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.admin',
        'django.contrib.admindocs',
        'django_extensions',
        'tardis.tardis_portal',
        'tardis.tardis_portal.templatetags',
        'registration',
        'django_nose',

) + apps

# LDAP configuration
LDAP_USE_TLS = False
LDAP_URL = "ldap://localhost:38911/"

LDAP_USER_LOGIN_ATTR = "uid"
LDAP_USER_ATTR_MAP = {"givenName": "display", "mail": "email"}
LDAP_GROUP_ID_ATTR = "cn"
LDAP_GROUP_ATTR_MAP = {"description": "display"}

#LDAP_ADMIN_USER = ''
#LDAP_ADMIN_PASSWORD = ''
LDAP_BASE = 'dc=example, dc=com'
LDAP_USER_BASE = 'ou=People, ' + LDAP_BASE
LDAP_GROUP_BASE = 'ou=Group, ' + LDAP_BASE

SYSTEM_LOG_LEVEL = 'INFO'
MODULE_LOG_LEVEL = 'INFO'

SYSTEM_LOG_FILENAME = 'request.log'
MODULE_LOG_FILENAME = 'tardis.log'

SYSTEM_LOG_MAXBYTES = 0
MODULE_LOG_MAXBYTES = 0

UPLOADIFY_PATH = '%s%s' % (MEDIA_URL, 'js/uploadify/')
UPLOADIFY_UPLOAD_PATH = '%s%s' % (MEDIA_URL, 'uploads/')

DEFAULT_INSTITUTION = "RMIT University"

IMMUTABLE_METS_DATASETS = True
# Settings for the single search box
# Set HAYSTACK_SOLR_URL to the location of the SOLR server instance
SINGLE_SEARCH_ENABLED = False 
HAYSTACK_SITECONF = 'tardis.search_sites'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = 'http://127.0.0.1:8080/solr'
if not SINGLE_SEARCH_ENABLED:
    HAYSTACK_ENABLE_REGISTRATIONS = False

PUBLISH_PROVIDERS = (
                 #   'tardis.tardis_portal.publish.rif_cs_profile.'
                 #   + 'rif_cs_PublishProvider.rif_cs_PublishProvider',
                    'tardis.apps.hpctardis.publish.rif_cs_profile.'
                    + 'rif_cs_PublishProvider.rif_cs_PublishProvider',
                    )
 

# --------------------------------------
# -- MicroTardis settings for testing --
# --------------------------------------

# Post Save Filters
POST_SAVE_FILTERS = [
    ("tardis.apps.microtardis.filters.exiftags.make_filter", ["MICROSCOPY_EXIF","http://rmmf.isis.rmit.edu.au/schemas"]),
    ("tardis.apps.microtardis.filters.spctags.make_filter", ["EDAXGenesis_SPC","http://rmmf.isis.rmit.edu.au/schemas"]),
    ("tardis.apps.hpctardis.filters.metadata.make_filter", ["",""])
 ]

# Directory path for storing image thumbnails
THUMBNAILS_PATH = path.abspath(path.join(path.dirname(__file__),
    '../var/thumbnails/')).replace('\\', '/')
    
# Template loaders
TEMPLATE_LOADERS = (
    'tardis.apps.microtardis.templates.loaders.app_specific.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.filesystem.Loader',
)

# Microtardis Media
MT_STATIC_URL_ROOT = '/static'
MT_STATIC_DOC_ROOT = path.join(path.dirname(__file__),
                               'apps/microtardis/static').replace('\\', '/')
                               
                               
# ------------------------------------
# -- HPCTardis settings for testing --
# ------------------------------------

tmp = list(POST_SAVE_FILTERS)
tmp.append(("tardis.apps.hpctardis.filters.metadata.make_filter", ["",""]))
POST_SAVE_FILTERS = tuple(tmp)

INSTALLED_APPS = (TARDIS_APP_ROOT+".hpctardis",) + INSTALLED_APPS


# The anzsrc codes for subject for all collections
COLLECTION_SUBJECTS = None
GROUP = "Acme University"
GROUP_ADDRESS = "Acme University, Coimbatore, India"
ACCESS_RIGHTS= "Contact the researchers/parties associated with this dataset"
RIGHTS= "Terms and conditions applies as specified by the researchers"



# HPCTardis Media
HPC_STATIC_URL_ROOT = '/static'
HPC_STATIC_DOC_ROOT = path.join(path.dirname(__file__),
                               'apps/hpctardis/static').replace('\\', '/')

# Changed because hpctardis overrides existing urls, which are called in testcases
ROOT_URLCONF = 'tardis.apps.hpctardis.urls'

PRIVATE_DATAFILES = False
                     
MATPLOTLIB_HOME = path.abspath(path.join(path.dirname(__file__), 
                                         '../../../db')).replace('\\', '/')