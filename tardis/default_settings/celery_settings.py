# Celery queue
from datetime import timedelta
from kombu import Exchange, Queue

# https://docs.celeryproject.org/en/stable/userguide/configuration.html
# Celery will still be able to read old configuration files until Celery 6.0.
# Afterwards, support for the old configuration files will be removed.

# Using Celery for asynchronous task processing requires a broker e.g. RabbitMQ
# Use a strong password for production
broker_url = 'amqp://%(user)s:%(password)s@%(host)s:%(port)s/%(vhost)s' % {
    'host': 'localhost',
    'port': 5672,
    'user': 'guest',
    'password': 'guest',
    'vhost': '/'
}

# Where to send task state and results
result_backend = 'rpc://'

# List of modules to import when the Celery worker starts
imports = ('tardis.tardis_portal.tasks',)

# These settings help with task prioritization:
task_acks_late = True
worker_prefetch_multiplier = 1

MAX_TASK_PRIORITY = 10
DEFAULT_TASK_PRIORITY = 5
DEFAULT_EMAIL_TASK_PRIORITY = 10

task_default_queue = 'celery'
# The 'x-max-priority' argument will only be respected by the RabbitMQ broker,
# which is the recommended broker for MyTardis:
task_queues = (
    Queue('celery', Exchange('celery'),
          routing_key='celery',
          queue_arguments={'x-max-priority': MAX_TASK_PRIORITY}),
)

beat_schedule = {
    "verify-files": {
        "task": "tardis_portal.verify_dfos",
        "schedule": timedelta(seconds=300),
        "kwargs": {'priority': DEFAULT_TASK_PRIORITY}
    }
}

# For local development, you can force Celery tasks to run synchronously:
# task_always_eager = True
# task_eager_propagates = True
