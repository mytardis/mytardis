import logging
from os import path

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = ':memory:'
ROOT_URLCONF = 'tardis.urls'
DEBUG = True
STATIC_DOC_ROOT = path.join(path.abspath(path.dirname(__file__)),
                            'tardis_portal/site_media')

FILE_STORE_PATH = path.abspath(path.join(path.dirname(__file__),
                                         '../var/store/'))
STAGING_PATH = path.abspath(path.join(path.dirname(__file__),
                                      "../var/staging/"))

ADMIN_MEDIA_STATIC_DOC_ROOT = ''
HANDLEURL = ''
SITE_ID = '1'
MEDIA_URL = '/site_media/'
TEMPLATE_DIRS = ['.']

# TODO: move vbl auth provider settings to mecat module
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

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tardis.tardis_portal.auth.AuthorizationMiddleware',
    'tardis.tardis_portal.minidetector.Middleware'
)

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
        'tardis.apps.equipment',
        'registration',
        'django_nose',
        'south'
)

# TODO: move to mecat settings module
VBLSTORAGEGATEWAY = \
'https://vbl.synchrotron.org.au/StorageGateway/VBLStorageGateway.wsdl'


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


TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

LOG_FILENAME = None
# LOG_FILENAME = '/var/log/tardis/tardis.log'

LOG_FORMAT = "%(asctime)s - %(levelname)-8s - %(message)s"

# logging levels are: DEBUG, INFO, WARN, ERROR, CRITICAL
LOG_LEVEL = logging.ERROR
