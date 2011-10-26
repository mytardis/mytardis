from os import path
from settings_changeme import *

# Add site specific changes here.

# Turn on django debug mode.
DEBUG = True

# Use the built-in SQLite database for testing.
# The database needs to be named something other than "tardis" to avoid
# a conflict with a directory of the same name.
DATABASES['default']['NAME'] = 'tardis_db'
DATABASES['default']['USER'] = 'tardis'
DATABASES['default']['PASSWORD'] = 'tardis'
DATABASES['default']['HOST'] = 'localhost'

RIFCS_PROVIDERS = ('tardis.tardis_portal.publish.provider.anstorifcsprovider.AnstoRifCsProvider',
                   'tardis.tardis_portal.publish.provider.synchrotronrifcsprovider.SynchrotronRifCsProvider')