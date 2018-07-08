# pylint: disable=wildcard-import,unused-wildcard-import

from os import listdir

from celery import Celery
from django.apps import apps  # pylint: disable=wrong-import-order

from .default_settings import *  # noqa # pylint: disable=W0401,W0614
import logging  # pylint: disable=wrong-import-order

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

DEBUG = True

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
BROKER_URL = 'memory://'
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
tardis_portal_app = Celery('tardis_portal')
tardis_portal_app.config_from_object('django.conf:settings')
tardis_portal_app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])

TEMPLATES[0]['DIRS'].append('.')
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

del STATICFILES_STORAGE  # noqa

STAGING_PATH = path.abspath(path.join(path.dirname(__file__),
                                      "../var/test/staging/"))
DEFAULT_STORAGE_BASE_DIR = path.abspath(path.join(path.dirname(__file__),
                                        '../var/store/')).replace('\\', '/')

STAGING_PROTOCOL = 'localdb'

GET_FULL_STAGING_PATH_TEST = path.join(STAGING_PATH, "test_user")

AUTH_PROVIDERS = (('localdb', 'Local DB',
                  'tardis.tardis_portal.auth.localdb_auth.DjangoAuthBackend'),
                  ('vbl', 'VBL',
                   'tardis.tardis_portal.tests.mock_vbl_auth.MockBackend'),
                  ('ldap', 'LDAP',
                   'tardis.tardis_portal.auth.ldap_auth.ldap_auth'))

#if (optional) ldap doesn't exist then don't enable ldap auth
try:
    import ldap  # noqa # pylint: disable=C0411,C0413,W0611
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
                filter(path.isdir,
                       map(lambda name: path.join(tardis_app_dir, name),
                           listdir(tardis_app_dir))))
    return tuple(sorted(map(lambda name: name.replace(path.sep, '.'), names)))

INSTALLED_APPS += get_all_tardis_apps() + (
    'tardis.apps.equipment',
    'django_nose',
    'behave_django',
)

DEDUP_INSTALLED_APPS = []
for app in INSTALLED_APPS:
    if app not in DEDUP_INSTALLED_APPS:
        DEDUP_INSTALLED_APPS.append(app)
INSTALLED_APPS = tuple(DEDUP_INSTALLED_APPS)

# LDAP configuration
LDAP_USE_TLS = False
LDAP_URL = "ldap://localhost:38911/"

LDAP_USER_LOGIN_ATTR = "uid"
LDAP_USER_ATTR_MAP = {"givenName": "first_name", "sn": "last_name", "mail": "email"}
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
OAI_DOCS_PATH = '/tmp/mytardis/rifcs'
RIFCS_TEMPLATE_DIR = 'tardis/tardis_portal/tests/rifcs/'
RIFCS_GROUP = 'MyTardis Test Group'
RIFCS_KEY = "keydomain.test.example"

# tardis.apps.sync
MYTARDIS_SITES_URL = 'http://localhost:8080/mytardis-sites.xml/'
MYTARDIS_SITE_URL = 'http://localhost:8080/'
SYNC_MANAGER = 'managers.default_manager'

SYNC_CLIENT_KEYS = (
    ('127.0.0.1', 'valid_client_key'),
        )

SYNC_CLIENT_KEY = 'valid_client_key'

SYNC_ADMINS = ('syncadmin@localhost', )
SERVER_EMAIL = 'transfers@localhost'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

REMOTE_SERVER_CREDENTIALS = [
    # Just one server for tests
    ('http://localhost:4272/', 'username', 'password')
]

REQUIRE_DATAFILE_CHECKSUMS = True
REQUIRE_DATAFILE_SIZES = True
REQUIRE_VALIDATION_ON_INGESTION = True

ARCHIVE_FILE_MAPPERS = {
    'deep-storage': (
        'tardis.apps.deep_storage_download_mapper.mapper.deep_storage_mapper',
    ),
}

# Site's default archive organization (i.e. path structure)
DEFAULT_ARCHIVE_ORGANIZATION = 'deep-storage'

DEFAULT_ARCHIVE_FORMATS = ['tar']

AUTOGENERATE_API_KEY = True

MIDDLEWARE += ('tardis.tardis_portal.filters.FilterInitMiddleware',)

SECRET_KEY = 'ij!%7-el^^rptw$b=iol%78okl10ee7zql-()z1r6e)gbxd3gl'

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
USE_TZ = True  # apparently sqlite has issues with timezones?

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.BaseSignalProcessor'

# Only for automated testing - don't use this in production:
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
