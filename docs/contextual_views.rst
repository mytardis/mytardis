================
Contextual Views
================

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

    DATAFILE_VIEWS = [("http://example.org/views/awesome_view",
                       "/apps/awesome-view/view"),]

Currently, the default view is always ``DataFile`` metadata. This
can be changed, for example, by developing a custom ``Dataset`` view,
which is explained in the following chapter.

Dataset and Experiment Views
============================

Rationale
---------

For some specific uses the data available can be presented and/or
processed in useful ways. The example that this feature was built for
are single-image and many-image datasets from the Australian
Synchrotron. Single images can be displayed large and for a many-image
dataset it is more useful to show a couple of example images taken at
regular intervals not from the beginning of the set of files.  These
different datasets can be tagged differently and subsequently
displayed differently.

User Guide
----------

Similarly to contextual ``DataFile`` views, ``Dataset`` and ``Experiment``
views rely on specific schemas attached to them.

The schema for each view either needs to be created and attached to a
Dataset, or the view can be set up for Dataset schemas that are
already in use.

There are two main differences:

* instead of an AJAX-loaded URL the settings associate a view function
  with a schema.

  Example:

::

    DATASET_VIEWS = [
        ("http://example.org/awesome_data/1",
         "tardis.apps.mx_views.views.view_full_dataset"),
    ]
    EXPERIMENT_VIEWS = [
        ("http://example.org/awesome_experiments/1",
         "tardis.apps.mx_views.views.view_fancy_experiment"),
    ]


* there is currently no UI choice of the ``Dataset`` and ``Experiment`` views.

Good practice
-------------

The default and well-tested ``Dataset`` and ``Experiment`` views can be
changed minimally for specific purposes by extending the default template
and overriding a template block.

New versions may change the default view functions. If you copy and paste them
for your application, please check with each upgrade that you are still using
up to date code.
