from tardis.default_settings.apps import INSTALLED_APPS

# Settings for the single search box
SINGLE_SEARCH_ENABLED = False
# flip this to turn on search:
if SINGLE_SEARCH_ENABLED:
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.elasticsearch_backend.'
                      'ElasticsearchSearchEngine',
            'URL': 'http://127.0.0.1:9200/',
            'INDEX_NAME': 'haystack',
        },
    }
else:
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
        },
    }
if SINGLE_SEARCH_ENABLED:
    INSTALLED_APPS = INSTALLED_APPS + ('haystack',)
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
