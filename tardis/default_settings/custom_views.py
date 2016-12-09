
INDEX_VIEWS = {}
'''
A custom index page override is defined in as dictionary mapping a class-based
view (or view function) to a Django ``Site``, specified by SITE_ID (an integer)
or the domain name of the incoming request.
See: https://mytardis.readthedocs.org/en/develop/contextual_views.html#custom-index-view

eg:
::
        INDEX_VIEWS = {
            1: 'tardis.apps.my_custom_app.views.MyCustomIndexSubclass',
            'store.example.com': 'tardis.apps.myapp.AnotherCustomIndexSubclass'
        }
'''

DATASET_VIEWS = []
'''
Dataset view overrides ('contextual views') are specified as tuples mapping
a Schema namespace to a class-based view (or view function).
See: https://mytardis.readthedocs.org/en/develop/contextual_views.html#dataset-and-experiment-views

eg:
::
        DATASET_VIEWS = [
            ('http://example.org/schemas/dataset/my_awesome_schema',
             'tardis.apps.my_awesome_app.views.CustomDatasetViewSubclass'),
        ]
'''

EXPERIMENT_VIEWS = []
'''
Experiment view overrides ('contextual views') are specified as tuples mapping
a Schema namespace to a class-based view (or view function).
See: https://mytardis.readthedocs.org/en/develop/contextual_views.html#dataset-and-experiment-views

eg:
::
        EXPERIMENT_VIEWS = [
            ('http://example.org/schemas/expt/my_awesome_schema',
             'tardis.apps.my_awesome_app.views.CustomExptViewSubclass'),
        ]
'''
