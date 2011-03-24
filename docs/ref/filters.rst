.. _ref-filterframework:

:mod:`~tardis.tardis_portal.filters` -- Filter Framework
========================================================

.. py:module:: tardis.tardis_portal.filters
.. moduleauthor:: Russell Sim <russell.sim@monash.edu>


Filters are called once an object has been saved to the database, they
build on the Django signal infrastrcture.

In the *settings.py* file filters are activated by specifying them
within the **POST_SAVE_FILTERS** variable::

   POST_SAVE_FILTERS = [
       ("tardis.tardis_portal.filters.exif.EXIFFilter", ["EXIF", "http://exif.schema"]),
       ]

The format they are specified in is::

   (<filter class path>, [args], {kwargs})

Where **args** and **kwargs** are both optional.

Filter Plugins
--------------

* :py:class:`tardis.tardis_portal.filters.exif.make_filter`


.. py:currentmodule:: tardis.tardis_portal.filters.exif

EXIF Filter
-----------

.. autofunction:: make_filter

