================
Contextual Views
================

Introduction
============
In order to better represent specific data types and facilities, MyTardis
allows apps to override the default views for Experiments, Datasets,
DataFile metadata, and the main index page. The following sections detail
settings and requirements of apps to make this happen.

Datafile Views
==============

Rationale
---------

By default there exists an option to show the metadata of individual
``DataFile`` s in the default ``Dataset`` view. Some kinds of files
allow for rich and useful visualisation and/or processing. For this
purpose there exist contextual views, views that are available
depending on the type of file they refer to.

User Guide
----------

A default installation has no contextual views. To enable them a few
steps are needed:

* an app needs to be installed either in ``tardis/apps/``, or the app's
  configuration must subclass ``AbstractTardisAppConfig`` thereby enabling
  autodetection. ``AbstractTardisAppConfig`` replaces ``AppConfig`` as
  described in these
  `django docs <https://docs.djangoproject.com/en/1.8/ref/applications/>`_.

* ``DataFile`` s need to be manually or automatically tagged with a
  schema that identifies them as viewable with a particular
  view. Filters are a convenient way to do this. See below for an
  example.

* settings need to be added to settings.py. A list called
  ``DATAFILE_VIEWS`` holds a tuple for each available view. The first
  entry of the tuple is a schema namespace and is matched against all
  schemas attached to the ``DataFile``. If a match occurs, a link
  to the url given as second entry of the tuple is added to the
  Datafile Detail section of the default Dataset view and loaded via
  AJAX on demand. Example:

::

    DATAFILE_VIEWS = [("http://example.org/schemas/datafile/my_awesome_schema",
                       "/apps/my-awesome-app/view"),]

Currently, the default view is always ``DataFile`` metadata. This
can be changed, for example, by developing a custom ``Dataset`` view,
which is explained in the following section.

Dataset and Experiment Views
============================

Rationale
---------

For some specific uses the data available can be presented and/or
processed in useful ways. MyTardis allows views for Experiments and Datasets to
be overriden by apps on a per-schema basis, allowing custom views for specifc
data types. The example that this feature was built for are single-image and
many-image datasets from the Australian Synchrotron. Single images can be
displayed large and for a many-image dataset it is more useful to show a couple
of example images taken at regular intervals not from the beginning of the set
of files. These different datasets can be detected via their schema namespace
and displayed differently.

User Guide
----------

Akin to ``DataFile`` contextual views, ``Dataset`` and ``Experiment``
contextual views rely on matching a specific schema namespace in an attached
ParameterSet.

Existing schemas can be used, or a special schema intended only for tagging an
Experiment or Dataset for contextual view override can be attached (via an
otherwise empty ParameterSet).

``Dataset`` and ``Experiment`` contextual views are configured in settings by
 associating a schema namespace with a class-based view (or view function).
Unlike ``DataFile`` contextual views which inject content into the DOM via an
AJAX call, these contextual views override the entire page.

  Example:

::

    DATASET_VIEWS = [
        ('http://example.org/schemas/dataset/my_awesome_schema',
         'tardis.apps.my_awesome_app.views.CustomDatasetViewSubclass'),
    ]

    EXPERIMENT_VIEWS = [
        ('http://example.org/schemas/expt/my_awesome_schema',
         'tardis.apps.my_awesome_app.views.CustomExptViewSubclass'),
    ]

Custom Index View
=================

Rationale
---------
Specific sites or facilities often want to display a custom index page that
presents recently ingested experiments in a way which is more meaningful for
their particular domain or application. MyTardis support overriding the
index page (/) on a per-domain or per-``Site`` basis.

User Guide
----------

Example:
::

    INDEX_VIEWS = {
        1: 'tardis.apps.my_custom_app.views.MyCustomIndexSubclass',
        'facility.example.org': 'tardis.apps.myapp.AnotherCustomIndexSubclass'
    }

A custom view override is defined in settings as dictionary mapping a
class-based view (or view function) to a Django
`Site <https://docs.djangoproject.com/en/1.8/ref/contrib/sites/>`_. A ``Site`` is
specified by SITE_ID (an integer) or the domain name of the incoming request.

Developers creating custom contextual index views are encouraged to subclass
``tardis.tardis_portal.views.pages.IndexView``.

Good practice for app developers
================================

In order to benefit from future bug and security fixes in core MyTardis, app
developers are strongly encouraged to override ``IndexView``, ``DatasetView``
and ``ExperimentView`` (from ``tardis.tardis_portal.pages``) when creating
custom contextual views.

The default and well-tested ``index.html``, ``view_dataset.html`` and
``view_experiment.html`` templates can used as a basis for these custom
contextual views.

New versions may change the default templates and view functions. If you copy
and paste parts for your application, please check with each upgrade that you
are still using up to date code.
