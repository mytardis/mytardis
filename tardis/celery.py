from __future__ import absolute_import
from datetime import timedelta
from celery import Celery  # pylint: disable=import-error
from django.apps import apps  # pylint: disable=wrong-import-order

tardis_app = Celery('tardis')
tardis_app.config_from_object('django.conf:settings')
tardis_app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])

tardis_app.conf.CELERYBEAT_SCHEDULE = {
    "verify-files": {
        "task": "tardis_portal.verify_dfos",
        "schedule": timedelta(seconds=300)
    },
}
