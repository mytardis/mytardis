DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = ':memory:'
ROOT_URLCONF = 'tardis.urls'
DEBUG = True
STATIC_DOC_ROOT = 'tardis_portal/site_media'
ADMIN_MEDIA_STATIC_DOC_ROOT = ''
HANDLEURL = ''
SITE_ID = '1'
TEMPLATE_DIRS = ['.','tardis_portal/']

MIDDLEWARE_CLASSES = ('django.middleware.common.CommonMiddleware',
                      'django.contrib.sessions.middleware.SessionMiddleware',
                      'django.contrib.auth.middleware.AuthenticationMiddleware',
                      'tardis.tardis_portal.minidetector.Middleware')

INSTALLED_APPS = ['tardis.tardis_portal',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.admin',
        'django.contrib.admindocs',
        'django_nose',
        'django_extensions',
        'registration',
        'tardis.tardis_portal.templatetags',
        ]
TEST_RUNNER = 'django_nose.run_tests'
