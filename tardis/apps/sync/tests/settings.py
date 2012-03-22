MYTARDIS_SITES_URL = 'http://localhost:8080/mytardis-sites.xml/'
SYNC_MANAGER = 'managers.default_manager'

# URL for this MyTardis instance. This should probably be renamed...
MYTARDIS_SITE_URL = 'http://localhost:8000'

from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    "runs-every-30-seconds": {
        "task": "tardis.apps.sync.tasks.clock_tick",
        "schedule": timedelta(seconds=10),
#        "args": ()
    },
}

