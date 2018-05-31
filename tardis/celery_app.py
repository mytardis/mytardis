from celery import Celery
from django.apps import apps

celery_app = Celery('tardis_portal')
celery_app.config_from_object('django.conf:settings')
celery_app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])
