DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = '/tmp/shorturls.db'
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
        'test_extensions',
        'tardis.tardis_portal.templatetags',]
