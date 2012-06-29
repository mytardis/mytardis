from os import listdir, path
import logging
import djcelery

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

# We're leaving this off for now, as most sites will until they convert DBs
USE_TZ = False

# Test timezone is GMT+10:00
# http://twiki.org/cgi-bin/xtra/tzdate?tz=Etc/GMT-10
TIME_ZONE = 'Etc/GMT-10'

DATE_FORMAT = "c"
DATETIME_FORMAT = "r"

# Celery queue uses Django for persistence
BROKER_TRANSPORT = 'django'
# During testing it's always eager
CELERY_ALWAYS_EAGER = True

ROOT_URLCONF = 'tardis.urls'

FILE_STORE_PATH = path.abspath(path.join(path.dirname(__file__),
                                         '../var/test/store/'))
STAGING_PATH = path.abspath(path.join(path.dirname(__file__),
                                      "../var/test/staging/"))
SYNC_TEMP_PATH = path.abspath(path.join(path.dirname(__file__),
                                        '../var/test/sync/'))

STAGING_PROTOCOL = 'localdb'
STAGING_MOUNT_PREFIX = 'smb://localhost/staging/'

GET_FULL_STAGING_PATH_TEST = path.join(STAGING_PATH, "test_user")

SITE_ID = '1'

# We get a warning if we don't define a secret
SECRET_KEY = 'this_is_a_secret_you_really_should_not_copy'

TEMPLATE_DIRS = ['.']

STATIC_DOC_ROOT = path.join(path.dirname(__file__),
                            'tardis_portal/site_media').replace('\\', '/')

DEFAULT_FILE_STORAGE = 'tardis.tardis_portal.storage.MyTardisLocalFileSystemStorage'
MEDIA_ROOT = FILE_STORE_PATH

MEDIA_URL = None
STATIC_URL = '/static/'

def get_admin_media_path():
    import pkgutil
    package = pkgutil.get_loader("django.contrib.admin")
    return path.join(package.filename, 'media')

ADMIN_MEDIA_STATIC_DOC_ROOT = get_admin_media_path()

AUTH_PROFILE_MODULE = 'tardis_portal.UserProfile'

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
                    'tardis.tardis_portal.auth.token_auth.TokenGroupProvider',
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
    'django.middleware.transaction.TransactionMiddleware'
)

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

TARDIS_APP_ROOT = 'tardis.apps'

def get_all_tardis_apps():
    base_dir = path.join(path.dirname(__file__), '..')
    tardis_app_dir = path.join(base_dir, *TARDIS_APP_ROOT.split('.'))
    names = map(lambda name: path.relpath(name, base_dir),
                filter(path.isdir, \
                       map(lambda name: path.join(tardis_app_dir, name),
                           listdir(tardis_app_dir))))
    return sorted(map(lambda name: name.replace(path.sep, '.') , names))

INSTALLED_APPS = get_all_tardis_apps() + [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_extensions',
    'tardis.tardis_portal',
    'tardis.tardis_portal.templatetags',
    'registration',
    'django_nose',
    'django_jasmine',
    'djcelery',
    'djkombu',
    'bootstrapform',
    'mustachejs',
]

JASMINE_TEST_DIRECTORY = path.abspath(path.join(path.dirname(__file__),
                                                'tardis_portal',
                                                'tests',
                                                'jasmine'))

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

SYSTEM_LOG_MAXBYTES = 0
MODULE_LOG_MAXBYTES = 0

UPLOADIFY_PATH = '%s/%s' % (STATIC_URL, 'js/uploadify/')
UPLOADIFY_UPLOAD_PATH = '%s/%s' % (MEDIA_URL, 'uploads/')

DEFAULT_INSTITUTION = "Monash University"

IMMUTABLE_METS_DATASETS = True

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

TOKEN_EXPIRY_DAYS = 30
TOKEN_LENGTH = 30
TOKEN_USERNAME = 'tokenuser'

REQUIRE_VALID_PUBLIC_CONTACTS = True

# RIF-CS Settings
OAI_DOCS_PATH = 'tardis/tardis_portal/tests/rifcs/'
RIFCS_TEMPLATE_DIR = 'tardis/tardis_portal/tests/rifcs/'
RIFCS_GROUP='MyTardis Test Group'
RIFCS_KEY = "keydomain.test.example"
RELATED_INFO_SCHEMA_NAMESPACE = 'http://www.tardis.edu.au/schemas/related_info/2011/11/10'

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


djcelery.setup_loader()

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
