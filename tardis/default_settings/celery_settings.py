# Celery queue
from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    "verify-files": {
        "task": "tardis_portal.verify_dfos",
        "schedule": timedelta(seconds=300)
    },
}

CELERY_IMPORTS = ('tardis.tardis_portal.tasks',)

# Use a real broker (e.g. RabbitMQ) for production, but memory is OK for
# local development:
BROKER_URL = 'memory://'

# For local development, you can force Celery tasks to run synchronously:
# CELERY_ALWAYS_EAGER = True
# CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
