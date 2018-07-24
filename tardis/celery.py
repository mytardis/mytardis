from __future__ import absolute_import
from celery import Celery  # pylint: disable=import-error
from django.apps import apps  # pylint: disable=wrong-import-order

tardis_app = Celery('tardis')
tardis_app.config_from_object('django.conf:settings')
tardis_app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])
