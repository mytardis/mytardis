# Celery queue
from datetime import timedelta

from celery import Celery
from django.apps import apps  # pylint: disable=wrong-import-order

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

celery_app = Celery('tardis_portal')
celery_app.config_from_object('django.conf:settings')
celery_app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])
