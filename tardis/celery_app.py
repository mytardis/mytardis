from celery import Celery
from django.apps import apps  # pylint: disable=wrong-import-order

tardis_portal_app = Celery('tardis_portal')
tardis_portal_app.config_from_object('django.conf:settings')
tardis_portal_app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])
