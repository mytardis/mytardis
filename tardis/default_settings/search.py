import os

from .apps import INSTALLED_APPS

SINGLE_SEARCH_ENABLED = False
if SINGLE_SEARCH_ENABLED:
    INSTALLED_APPS += ('django_elasticsearch_dsl',)
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')
        }
    }
    ELASTICSEARCH_DSL_INDEX_SETTINGS = {
        'number_of_shards': 1
    }
