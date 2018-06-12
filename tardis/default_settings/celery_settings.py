# Celery queue
from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    "verify-files": {
        "task": "tardis_portal.verify_dfos",
        "schedule": timedelta(seconds=300)
    },
}

CELERY_IMPORTS = ('tardis.tardis_portal.tasks',)
