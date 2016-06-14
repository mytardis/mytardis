.. _ref-filterframework:

Filter Setup
============

:mod:`~tardis.tardis_portal.filters`


Filters are called once an object has been saved to the database. They
build on the `Django Signals Infrastructure`_.

In the *settings.py* file filters are activated by specifying them
within the ``POST_SAVE_FILTERS`` variable, for example

.. code-block:: python

   POST_SAVE_FILTERS = [
       ("tardis.tardis_portal.filters.exif.EXIFFilter",
        ["EXIF", "http://exif.schema"]),
   ]

The format they are specified in is

.. code-block:: python

   (<filter class path>, [args], {kwargs})

Where ``args`` and ``kwargs`` are both optional.

.. _`Django Signals Infrastructure`: https://docs.djangoproject.com/en/dev/topics/signals/

