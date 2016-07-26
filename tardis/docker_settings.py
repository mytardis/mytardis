# pylint: disable=wildcard-import,unused-wildcard-import
import os
import dj_database_url
from tardis.default_settings import *

DEBUG = bool(os.getenv('DEBUG', False))

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

DATABASES['default'] = dj_database_url.parse(os.environ['DATABASE_URL'],
                                             conn_max_age=600)

STATIC_ROOT = '/static/'

BROKER_URL = os.getenv('BROKER_URL')

# Don't use pickle as serializer, json is safer
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['application/json']

SITE_TITLE = os.getenv('SITE_TITLE', 'MyTardis')
SPONSORED_TEXT = os.getenv('SPONSORED_TEXT', None)
DEFAULT_INSTITUTION = os.getenv('DEFAULT_INSTITUTION', 'Monash University')
