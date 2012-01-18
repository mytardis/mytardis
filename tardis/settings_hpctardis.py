# Note that this is a deployment script with hardcoded paths

from os import path
from tardis.settings_changeme import *

# Database settings
DATABASES = {
    'default': {
        # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.sqlite3',
        # Name of the database to use. For SQLite, it's the full path.
        'NAME': '/home/user/CoreTardis/tardis.sql',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Root URLs in MicroTardis
ROOT_URLCONF = 'tardis.apps.hpctardis.urls'

# extend template directory to TEMPLATE_DIRS
tmp = list(TEMPLATE_DIRS)
tmp.append(path.join(path.dirname(__file__),
                     'apps/hpctardis/publish/').replace('\\', '/'),
    )
tmp.append(path.join(path.dirname(__file__),
                     'tardis_portal/publish/').replace('\\', '/'),
    )
TEMPLATE_DIRS = tuple(tmp)

# Post Save Filters
tmp = list(POST_SAVE_FILTERS)
tmp.append(("tardis.apps.microtardis.filters.exiftags.make_filter", ["MICROSCOPY_EXIF","http://rmmf.isis.rmit.edu.au/schemas"]))
tmp.append(("tardis.apps.microtardis.filters.spctags.make_filter", ["EDAXGenesis_SPC","http://rmmf.isis.rmit.edu.au/schemas"]))
tmp.append(("tardis.apps.hpctardis.filters.metadata.make_filter", ["",""]))
POST_SAVE_FILTERS = tuple(tmp)


ADMIN_MEDIA_STATIC_DOC_ROOT = path.join(path.dirname(__file__),'../eggs/Django-1.3-py2.6.egg/django/contrib/admin/media/').replace('\\', '/')

STAGING_PATH = path.abspath('/home/user/dcweb.staging/').replace('\\', '/')
STAGING_PROTOCOL = 'localdb'

# Directory path for image thumbnails
THUMBNAILS_PATH = path.abspath(path.join(path.dirname(__file__),
    '../var/thumbnails/')).replace('\\', '/')

INSTALLED_APPS = (TARDIS_APP_ROOT+".hpctardis",) + INSTALLED_APPS

# Template loaders
TEMPLATE_LOADERS = (
    'tardis.apps.microtardis.templates.loaders.app_specific.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.filesystem.Loader',
)


# logging levels are: DEBUG, INFO, WARN, ERROR, CRITICAL
SYSTEM_LOG_LEVEL = 'INFO'
MODULE_LOG_LEVEL = 'INFO'

SYSTEM_LOG_FILENAME = '/var/www/tardis/request.log'
MODULE_LOG_FILENAME = '/var/www/tardis/tardis.log'

EMAIL_PORT = 587 
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'eresearch.rmit@gmail.com'     
EMAIL_HOST_PASSWORD = 'PASSWORD'
EMAIL_USE_TLS = True
EMAIL_LINK_HOST = "http://gaia1.isis.rmit.edu.au:8090"