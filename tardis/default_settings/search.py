'''
Settings for search
'''

SINGLE_SEARCH_ENABLED = True
'''
To enable search:

SINGLE_SEARCH_ENABLED = True
INSTALLED_APPS += ('django_elasticsearch_dsl', 'tardis.app.search')
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')
    }
}
ELASTICSEARCH_DSL_INDEX_SETTINGS = {
    'number_of_shards': 1,
    'number_of_replicas': 0
}
'''

ELASTICSEARCH_PARALLEL_INDEX_SETTINGS = {
    'chunk_size': 500,
    'thread_count': 4
}
'''
Setting for running elastic search index in parallel mode to get indexing speed boost while indexing
https://django-elasticsearch-dsl.readthedocs.io/en/latest/settings.html#elasticsearch-dsl-parallel
'''


MAX_SEARCH_RESULTS = 100
'''
Limits the maximum number of search results for each model (Experiment, Dataset and DataFile).
The default value of 100 means that a query could potentially return 300 results in total,
i.e. 100 experiments, 100 datasets and 100 datafiles.
'''
MIN_CUTOFF_SCORE = 0.0
'''
Filters results based on this value.
The default value of 0.0 means that nothing will be excluded from search results.
Set it to any number greater than 0.0 to filter out results.
'''
