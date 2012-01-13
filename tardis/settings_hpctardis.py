from os import path
from tardis.settings_changeme import *

# Database settings
DATABASES = {
    'default': {
        # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.sqlite3',
        # Name of the database to use. For SQLite, it's the full path.
        'NAME': './tardis.sql',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Root URLs in MicroTardis
ROOT_URLCONF = 'tardis.urls'

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

