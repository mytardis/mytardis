# Celery queue
from datetime import timedelta

from kombu import Exchange, Queue

CELERY_IMPORTS = ("tardis.tardis_portal.tasks",)

# Using Celery for asynchronous task processing requires a broker e.g. RabbitMQ
# Use a strong password for production
BROKER_URL = "amqp://guest:guest@localhost:5672//"

# For local development, you can force Celery tasks to run synchronously:
# CELERY_ALWAYS_EAGER = True
# CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# These settings help with task prioritization:
CELERY_ACKS_LATE = True
CELERYD_PREFETCH_MULTIPLIER = 1

MAX_TASK_PRIORITY = 10
DEFAULT_TASK_PRIORITY = 5
DEFAULT_EMAIL_TASK_PRIORITY = 10

CELERY_DEFAULT_QUEUE = "celery"
# The 'x-max-priority' argument will only be respected by the RabbitMQ broker,
# which is the recommended broker for MyTardis:
CELERY_QUEUES = (
    Queue(
        "celery",
        Exchange("celery"),
        routing_key="celery",
        queue_arguments={"x-max-priority": MAX_TASK_PRIORITY},
    ),
)

CELERYBEAT_SCHEDULE = {
    "verify-files": {
        "task": "tardis_portal.verify_dfos",
        "schedule": timedelta(seconds=300),
        "kwargs": {"priority": DEFAULT_TASK_PRIORITY},
    }
}
