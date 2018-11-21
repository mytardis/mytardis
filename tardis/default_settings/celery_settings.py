# Celery queue
from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    "verify-files": {
        "task": "tardis_portal.verify_dfos",
        "schedule": timedelta(seconds=300)
    },
}

CELERY_IMPORTS = ('tardis.tardis_portal.tasks',)

# Using Celery for asynchronous task processing requires a broker e.g. RabbitMQ
# Use a strong password for production
BROKER_URL = 'amqp://guest:guest@localhost:5672//'

# For local development, you can force Celery tasks to run synchronously:
# CELERY_ALWAYS_EAGER = True
# CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
