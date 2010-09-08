DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = ':memory:'
ROOT_URLCONF = 'tardis_portal.urls'
DEBUG = True
STATIC_DOC_ROOT = 'tardis_portal/site_media'
ADMIN_MEDIA_STATIC_DOC_ROOT = ''
HANDLEURL = ''
SITE_ID = '1'
TEMPLATE_DIRS = ['.','tardis_portal/']
INSTALLED_APPS = ['tardis.tardis_portal',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.admin',
        'django.contrib.admindocs',
        'django_nose',
        'tardis.tardis_portal.templatetags',]
TEST_RUNNER = 'django_nose.run_tests'
