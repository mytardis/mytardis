INDEX_VIEWS = {}
"""
A custom index page override is defined in as dictionary mapping a class-based
view (or view function) to a Django ``Site``, specified by SITE_ID (an integer)
or the domain name of the incoming request.
See: https://mytardis.readthedocs.io/en/develop/apps/contextual_views.html#custom-index-view

e.g.::

        INDEX_VIEWS = {
            1: 'tardis.apps.my_custom_app.views.MyCustomIndexSubclass',
            'store.example.com': 'tardis.apps.myapp.AnotherCustomIndexSubclass'
        }
"""

LOGIN_VIEWS = {}
"""
A custom login page override is defined in as dictionary mapping a class-based
view (or view function) to a Django ``Site``, specified by SITE_ID (an integer)
or the domain name of the incoming request.
See: https://mytardis.readthedocs.io/en/develop/apps/contextual_views.html#custom-login-view

e.g.::

        LOGIN_VIEWS = {
            1: 'tardis.apps.my_custom_app.views.MyCustomLoginSubclass',
            'store.example.com': 'tardis.apps.myapp.AnotherCustomLoginSubclass'
        }
"""

DATASET_VIEWS = []
"""
Dataset view overrides ('contextual views') are specified as tuples mapping
a Schema namespace to a class-based view (or view function).
See: https://mytardis.readthedocs.io/en/develop/apps/contextual_views.html#dataset-and-experiment-views

e.g.::

        DATASET_VIEWS = [
            ('http://example.org/schemas/dataset/my_awesome_schema',
             'tardis.apps.my_awesome_app.views.CustomDatasetViewSubclass'),
        ]
"""

EXPERIMENT_VIEWS = []
"""
Experiment view overrides ('contextual views') are specified as tuples mapping
a Schema namespace to a class-based view (or view function).
See: https://mytardis.readthedocs.io/en/develop/apps/contextual_views.html#dataset-and-experiment-views

e.g.::

        EXPERIMENT_VIEWS = [
            ('http://example.org/schemas/expt/my_awesome_schema',
             'tardis.apps.my_awesome_app.views.CustomExptViewSubclass'),
        ]
"""
