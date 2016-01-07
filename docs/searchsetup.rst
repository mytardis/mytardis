
========================
Setting up Single search
========================

Tardis comes with a single search option which provides users with a
search field that returns a list of matching Experiments, Datasets and
Datafiles.

The single search box uses Elasticsearc, with a django-haystack frontent, and
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

Other settings are shown below:

HAYSTACK_CONNECTIONS
~~~~~~~~~~~~~~~~~~~~

The default value is ::

   HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.elasticsearch_backend.'
                      'ElasticsearchSearchEngine',
            'URL': 'http://127.0.0.1:9200/',
            'INDEX_NAME': 'haystack',
        },
    }

HAYSTACK_SIGNAL_PROCESSOR
~~~~~~~~~~~~~~~~~~~~~~~~~

This setting determins when the information in Elasticsearch is updated.
The default value updates it in real time with db changes ::

    HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

A more performant implementation would trigger an update task on each db change.

Please see django-haystack documentation for further information:
http://haystacksearch.org


Updating Indexes
----------------

Once Elasticsearch is set up, and Single Search is enabled (i.e. the
``SINGLE_SEARCH_ENABLED`` option in settings is set to True) Haystack will
automatically register the addition of and changes to models and reflect
these in the search index. That is, as soon as a new instance of a model is
added to the database, or changes are made to an existing isntance, these
changes will be searchable.

If you're adding search to an existing deployment of Django then you'll need
to manually trigger a rebuild of the indexes (automatic indexing only happens
through signals when models are added or changed).

Haystack registers a number of management commands with the Django framework,
the import one here being the rebuild_index command. To rebuild, navigate to
your checkout and call the following command ::

    python mytardis.py rebuild_index

Haystack will then ask you to confirm your decision (Note: Rebuilding will
destroy your existing indexes, and will take a while for large datasets, so
be sure), and then start rebuilding.
