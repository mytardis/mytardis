# pylint: disable=wildcard-import,unused-wildcard-import
import os

from tardis.default_settings import *


def getenv(name, default=None):
    return os.getenv('MYTARDIS_%s' % name, default)

DEBUG = bool(getenv('DEBUG', False))

SECRET_KEY = getenv('DJANGO_SECRET_KEY')

DATABASES['default'] = {
    'ENGINE': 'django.db.backends.%s' %
              getenv('DB_ENGINE', 'postgresql_psycopg2'),
    # Name of the database to use. For SQLite, it's the full path.
    'NAME': getenv('DB_NAME', 'postgres'),
    'USER': getenv('DB_USER', 'postgres'),
    'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
    'HOST': getenv('DB_HOST', 'db'),
    'PORT': getenv('DB_PORT', ''),
    'CONN_MAX_AGE': 600,
}

STATIC_ROOT = '/static/'

BROKER_URL = getenv('BROKER_URL')

# Don't use pickle as serializer, json is safer
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['application/json']

SITE_TITLE = getenv('SITE_TITLE', 'MyTardis')
SPONSORED_TEXT = getenv('SPONSORED_TEXT', None)
DEFAULT_INSTITUTION = getenv('DEFAULT_INSTITUTION', 'Monash University')

elasticsearch_host = getenv('ES_HOST', None)
if elasticsearch_host is not None:
    SINGLE_SEARCH_ENABLED = True
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.elasticsearch_backend.'
                      'ElasticsearchSearchEngine',
            'URL': 'http://%(host)s:%(port)s/' % {
                'host': getenv('ES_HOST'),
                'port': getenv('ES_PORT', '9200'),
            },
            'INDEX_NAME': 'haystack',
        },
    }
