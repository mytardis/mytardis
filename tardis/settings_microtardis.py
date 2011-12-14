from os import path
from tardis.settings_changeme import *

DATABASES = {
    'default': {
        # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.sqlite3',
        # Name of the database to use. For SQLite, it's the full path.
        'NAME': '/var/www/tardis/db/tardis.sql',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

ROOT_URLCONF = 'tardis.apps.microtardis.urls'

# extend template directory to TEMPLATE_DIRS
tmp = list(TEMPLATE_DIRS)
tmp.append(
    path.join(path.dirname(__file__),
    'apps/microtardis/templates/').replace('\\', '/')
)
TEMPLATE_DIRS = tuple(tmp)

# Post Save Filters
POST_SAVE_FILTERS = [
    ("tardis.apps.microtardis.filters.exiftags.make_filter", ["MICROSCOPY_EXIF","http://rmmf.isis.rmit.edu.au/schemas"]),
    ("tardis.apps.microtardis.filters.spctags.make_filter", ["EDAXGenesis_SPC","http://rmmf.isis.rmit.edu.au/schemas"]),
    ]

SYSTEM_LOG_FILENAME = '/home/rmmf/CoreTardis/var/log/request.log'
MODULE_LOG_FILENAME = 'home/rmmf/CoreTardis/var/log/tardis.log'

DEFAULT_INSTITUTION = "RMIT Microscopy and Microanalysis Facility"

THUMBNAILS_PATH = path.abspath(path.join(path.dirname(__file__),
    '../var/thumbnails/')).replace('\\', '/')
