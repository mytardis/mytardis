from tardis.settings_changeme import *
from os import listdir
import logging

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

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

# During testing it's always eager
CELERY_ALWAYS_EAGER = True

ROOT_URLCONF = 'tardis.urls'

TEMPLATE_DIRS = ['.']

del(STATICFILES_STORAGE)

FILE_STORE_PATH = path.abspath(path.join(path.dirname(__file__),
                                         '../var/test/store/'))
STAGING_PATH = path.abspath(path.join(path.dirname(__file__),
                                      "../var/test/staging/"))
SYNC_TEMP_PATH = path.abspath(path.join(path.dirname(__file__),
                                        '../var/test/sync/'))
SYNC_LOCATION = "sync"
SYNC_LOCATION_URL = "http://example.com/sync"

STAGING_PROTOCOL = 'localdb'

GET_FULL_STAGING_PATH_TEST = path.join(STAGING_PATH, "test_user")

AUTH_PROVIDERS = (('localdb', 'Local DB',
                  'tardis.tardis_portal.auth.localdb_auth.DjangoAuthBackend'),
                  ('vbl', 'VBL',
                   'tardis.tardis_portal.tests.mock_vbl_auth.MockBackend'))

#if (optional) ldap doesn't exist then don't enable ldap auth
try:
    import ldap
    AUTH_PROVIDERS += (('ldap', 'LDAP',
                        'tardis.tardis_portal.auth.ldap_auth.ldap_auth'),)
except ImportError:
    pass

NEW_USER_INITIAL_GROUPS = ['test-group']

DOWNLOAD_PROVIDERS = (
    ('vbl', 'tardis.tardis_portal.tests.mock_vbl_download'),
)

def get_all_tardis_apps():
    base_dir = path.join(path.dirname(__file__), '..')
    tardis_app_dir = path.join(base_dir, *TARDIS_APP_ROOT.split('.'))
    names = map(lambda name: path.relpath(name, base_dir),
                filter(path.isdir, \
                       map(lambda name: path.join(tardis_app_dir, name),
                           listdir(tardis_app_dir))))
    return tuple(sorted(map(lambda name: name.replace(path.sep, '.') , names)))

INSTALLED_APPS += get_all_tardis_apps() + (
    'django_nose',
)

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

SYSTEM_LOG_LEVEL = logging.DEBUG
MODULE_LOG_LEVEL = logging.DEBUG

SYSTEM_LOG_FILENAME = 'request-test.log'
MODULE_LOG_FILENAME = 'tardis-test.log'

# RIF-CS Settings
OAI_DOCS_PATH = 'tardis/tardis_portal/tests/rifcs/'
RIFCS_TEMPLATE_DIR = 'tardis/tardis_portal/tests/rifcs/'
RIFCS_GROUP='MyTardis Test Group'
RIFCS_KEY = "keydomain.test.example"

# tardis.apps.sync
MYTARDIS_SITES_URL = 'http://localhost:8080/mytardis-sites.xml/'
MYTARDIS_SITE_URL = 'http://localhost:8080/'
SYNC_MANAGER = 'managers.default_manager'

SYNC_CLIENT_KEYS = (
        ('127.0.0.1', 'valid_client_key'),
        )

SYNC_CLIENT_KEY = 'valid_client_key'

SYNC_ADMINS = ( 'syncadmin@localhost', )
SERVER_EMAIL = 'transfers@localhost'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

REMOTE_SERVER_CREDENTIALS = [
    # Just one server for tests
    ('http://localhost:4272/', 'username', 'password')
]

INITIAL_LOCATIONS = [{'name': DEFAULT_LOCATION,
                      'url': 'file://' + FILE_STORE_PATH,
                      'provider': 'local',
                      'type': 'online',
                      'priority': 10},
                     {'name': 'sync',
                      'url': 'file://' + SYNC_TEMP_PATH,
                      'type': 'external',
                      'priority': 8},
                     {'name': 'staging',
                      'url': 'file://' + STAGING_PATH,
                      'type': 'external',
                      'priority': 5},
                     {'name': 'test',
                      'provider': 'http',
                      'params': {'trust_length': False,
                                 'metadata_supported': True},
                      'url': 'http://127.0.0.1:4272/data/',
                      'type': 'online',
                      'priority': 10},
                     {'name': 'test2',
                      'provider': 'dav',
                      'params': {'trust_length': False},
                      'url': 'http://127.0.0.1/data2/',
                      'type': 'online',
                      'priority': 10},
                     {'name': 'test3',
                      'provider': 'dav',
                      'params': {'trust_length': False,
                                 'user' : 'datameister',
                                 'password' : 'geheimnis',
                                 'auth' : 'basic',
                                 'realm' : 'wunderland'},
                      'url': 'http://127.0.0.1/data3/',
                      'type': 'online',
                      'priority': 10},
]

DEFAULT_MIGRATION_DESTINATION = 'test'

MIGRATION_SCORING_PARAMS = {
    'user_priority_weighting': [5.0, 2.0, 1.0, 0.5, 0.2],
    'file_size_threshold': 0,
    'file_size_weighting': 1.0,
    'file_access_threshold': 0,
    'file_access_weighting': 0.0,
    'file_age_threshold': 0,
    'file_age_weighting': 0.0}
REQUIRE_DATAFILE_CHECKSUMS = True
REQUIRE_DATAFILE_SIZES = True
REQUIRE_VALIDATION_ON_INGESTION = True

ARCHIVE_FILE_MAPPERS = {
    'test': ('tardis.tardis_portal.tests.test_download.MyMapper',),
    'test2': ('tardis.tardis_portal.tests.test_download.MyMapper',
              {'exclude': '.txt'})
}

DEFAULT_ARCHIVE_ORGANIZATION = 'test'
DEFAULT_ARCHIVE_FORMATS = ['tar', 'tgz']
