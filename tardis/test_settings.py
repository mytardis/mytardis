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

ROOT_URLCONF = 'tardis.urls'

FILE_STORE_PATH = path.abspath(path.join(path.dirname(__file__),
                                         '../var/store/'))
STAGING_PATH = path.abspath(path.join(path.dirname(__file__),
                                      "../var/staging/"))

STAGING_PROTOCOL = 'localdb'
STAGING_MOUNT_PREFIX = 'smb://localhost/staging/'

GET_FULL_STAGING_PATH_TEST = path.join(STAGING_PATH, "test_user")

SITE_ID = '1'

TEMPLATE_DIRS = ['.']

STATIC_DOC_ROOT = path.join(path.dirname(__file__),
                            'tardis_portal/site_media').replace('\\', '/')

MEDIA_ROOT = STATIC_DOC_ROOT

MEDIA_URL = '/site_media/'

ADMIN_MEDIA_STATIC_DOC_ROOT = path.join(path.dirname(__file__),
                                        '../parts/django/django/contrib/admin/media/').replace('\\', '/')


AUTH_PROVIDERS = (('localdb', 'Local DB',
                  'tardis.tardis_portal.auth.localdb_auth.DjangoAuthBackend'),
                  ('vbl', 'VBL',
                   'tardis.tardis_portal.tests.mock_vbl_auth.MockBackend'),
                  ('ldap', 'LDAP',
                   'tardis.tardis_portal.auth.ldap_auth.ldap_auth'),
)
DEFAULT_AUTH = 'localdb'

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
    'django.middleware.transaction.TransactionMiddleware'
)

TARDIS_APP_ROOT = 'tardis.apps'
TARDIS_APPS = ('equipment',)
#TARDIS_APPS = ()

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

SYSTEM_LOG_LEVEL = 'DEBUG'
MODULE_LOG_LEVEL = 'DEBUG'

SYSTEM_LOG_FILENAME = 'request.log'
MODULE_LOG_FILENAME = 'tardis.log'

SYSTEM_LOG_MAXBYTES = 0
MODULE_LOG_MAXBYTES = 0

UPLOADIFY_PATH = '%s%s' % (MEDIA_URL, 'js/uploadify/')
UPLOADIFY_UPLOAD_PATH = '%s%s' % (MEDIA_URL, 'uploads/')

DEFAULT_INSTITUTION = "Monash University"

IMMUTABLE_METS_DATASETS = True

# Settings for the single search box
# Set HAYSTACK_SOLR_URL to the location of the SOLR server instance
SINGLE_SEARCH_ENABLED = False
HAYSTACK_SITECONF = 'tardis.search_sites'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = 'http://127.0.0.1:8080/solr'
if not SINGLE_SEARCH_ENABLED:
    HAYSTACK_ENABLE_REGISTRATIONS = False
