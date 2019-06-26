
=================
Setting Up Search
=================

Tardis comes with a single search option which provides users with a
search field that returns a list of matching Experiments, Datasets and
Datafiles.

The single search box uses Elasticsearch, and Django Elasticsearch DSL library that allows
indexing of django models in elasticsearch, and
accordingly requires some setup.
The single search box is disabled by default.

Setting up Elasticsearch
========================
Elasticsearch doesn't work out of the box with MyTardis. It is not currently
installed with pip and requires a number of manual steps to get working.

Elasticsearch can be found here: https://www.elastic.co/products/elasticsearch

The following are a very simple list of steps that will get everything up and
running. It is advisable to follow up with the person responsible for
overseeing security policy at your home institution to see if any extra
setup is necessary.


Django Configuration
====================

Enabling Single Search
----------------------

A list of default settings for Single Search are already in default_settings.py
in the MyTardis repository. Single search is enabled by setting the
SINGLE_SEARCH_ENABLED option to True.

MyTardis comes with a search app that allows indexing Experiments, Dataset and Datafile models
and also provides view and api to perform elasticsearch query on these models. This can be
enabled by adding 'tardis.apps.search' to the list of installed apps.

Other settings are shown below:

ELASTICSEARCH_DSL Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~

The default value is

.. code-block:: python

    INSTALLED_APPS += ('django_elasticsearch_dsl','tardis.apps.search',)
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': 'http://localhost:9200'
        },
    }
    ELASTICSEARCH_DSL_INDEX_SETTINGS = {
        'number_of_shards': 1
    }


Updating Indexes
----------------

Once Elasticsearch is set up, and Single Search is enabled (i.e. the
``SINGLE_SEARCH_ENABLED`` option in settings is set to True) Elasticsearch DSL will
automatically register the addition of and changes to models and reflect
these in the search index. That is, as soon as a new instance of a model is
added to the database, or changes are made to an existing instance, these
changes will be searchable.

If you're adding search to an existing deployment of Django then you'll need
to manually trigger a rebuild of the indexes (automatic indexing only happens
through signals when models are added or changed).

Elasticsearch DSL registers a number of management commands with the Django framework,
these commands can be listed by running the following command ::

    python manage.py search_index --help

the important one here being the *--rebuild* command. To rebuild, navigate to
your checkout and call the following command ::

    python manage.py search_index --rebuild

Elasticsearch DSL will then ask you to confirm your decision (Note: Rebuilding will
destroy your existing indexes, and will take a while for large datasets, so
be sure), and then start rebuilding.
