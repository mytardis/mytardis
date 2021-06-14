# Celery queue
from datetime import timedelta
from kombu import Exchange, Queue

# https://docs.celeryproject.org/en/stable/userguide/configuration.html
# Celery will still be able to read old configuration files until Celery 6.0.
# Afterwards, support for the old configuration files will be removed.

# Using Celery for asynchronous task processing requires a broker e.g. RabbitMQ
# Use a strong password for production
CELERY_BROKER_URL = 'amqp://%(user)s:%(password)s@%(host)s:%(port)s/%(vhost)s' % {
    'host': 'localhost',
    'port': 5672,
    'user': 'guest',
    'password': 'guest',
    'vhost': '/'
}

# Where to send task state and results
CELERY_RESULT_BACKEND = 'rpc://'

# List of modules to import when the Celery worker starts
CELERY_IMPORTS = ('tardis.tardis_portal.tasks',)

# These settings help with task prioritization:
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

MAX_TASK_PRIORITY = 10
DEFAULT_TASK_PRIORITY = 5
DEFAULT_EMAIL_TASK_PRIORITY = 10

CELERY_TASK_DEFAULT_QUEUE = 'celery'
# The 'x-max-priority' argument will only be respected by the RabbitMQ broker,
# which is the recommended broker for MyTardis:
CELERY_TASK_QUEUES = (
    Queue('celery', Exchange('celery'),
          routing_key='celery',
          queue_arguments={'x-max-priority': MAX_TASK_PRIORITY}),
)

CELERY_BEAT_SCHEDULE = {
    "verify-files": {
        "task": "tardis_portal.verify_dfos",
        "schedule": timedelta(seconds=300),
        "kwargs": {'priority': DEFAULT_TASK_PRIORITY}
    }
}

# For local development, you can force Celery tasks to run synchronously:
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_EAGER_PROPAGATES = True
