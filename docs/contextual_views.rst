================
Contextual Views
================

Datafile Views
==============

Rationale
---------

By default there exists an option to show the metadata of individual
``Dataset_File`` s in the default ``Dataset`` view. Some kinds of files
allow for rich and useful visualisation and/or processing. For this
purpose there exist contextual views, views that are available
depending on the type of file they refer to.

User Guide
----------

A default installation has no contextual views. To enable them a few
steps are needed:

* an app needs to be installed in ``tardis/apps/``

* ``Dataset_File`` s need to be manually or automatically tagged with a
  schema that identifies them as viewable with a particular
  view. Filters are a convenient way to do this. See below for an
  example.

* settings need to be added to settings.py. A list called
  ``DATAFILE_VIEWS`` holds a tuple for each available view. The first
  entry of the tuple is a schema namespace and is matched against all
  schemas attached to the ``Dataset_File``. If a match occurs, a link
  to the url given as second entry of the tuple is added to the
  Datafile Detail section of the default Dataset view and loaded via
  AJAX on demand. Example:

::

    DATAFILE_VIEWS = [("http://example.org/views/awesome_view",
                       "/apps/awesome-view/view"),]

Currently, the default view is always ``Dataset_File`` metadata. This
can be changed, for example, by developing a custom ``Dataset`` view.

