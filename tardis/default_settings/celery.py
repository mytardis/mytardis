# Celery queue
from datetime import timedelta

import djcelery

BROKER_URL = 'django://'
'''
use django:, add kombu.transport.django to INSTALLED_APPS
or use redis: install redis separately and add the following to a
custom buildout.cfg:
    django-celery-with-redis
    redis
    hiredis
'''
# BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

CELERYBEAT_SCHEDULE = {
    "verify-files": {
        "task": "tardis_portal.verify_dfos",
        "schedule": timedelta(seconds=300)
    },
    # enable this task for the publication workflow
    # "update-publication-records": {
    #     "task": "apps.publication_forms.update_publication_records",
    #     "schedule": timedelta(seconds=300)
    # },
}

djcelery.setup_loader()
