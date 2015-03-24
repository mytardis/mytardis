=========
Ingesting
=========

There are four mechanisms for ingesting metadata and data into MyTARDIS:

#. User Interface
   The User Interface is appropriate for ingesting a single experiment by the
   end user with a relatively small amount of data.
#. REST API
   The RESTful API allows creation of Experiments, Datasets and Datafiles
   including meta data. Files can be added via POSTing, through a staging
   area or through a shared data storage area. See :doc:`api` for more
   information.
#. Staging Area
   The Staging Area is appropriate for ingesting a single experiment by the
   end user with larger amounts of data.
#. Batch Ingestion
   Batch ingestion is typically used by facilities automatically ingesting all
   metadata from one or more instruments into MyTARDIS.


Post Processing
---------------

MyTARDIS takes advantage of the Django signal framework to provide post
processing of files. The only default post processing step that is
enabled by default operates on newly created Dataset Files.


Staging Hook
^^^^^^^^^^^^

Currently, this functionality is being rewritten and hence disabled until the
new solution is usable.

The staging hook is responsible for moving files from the staging area
to the data store. It operates as a
:class:`django.db.models.signals.post_save` signal and only triggers
in a newly created file.

The staging hook is only triggerd on files that have a protocol of
`staging` which signifies that the file is in the in the TARDIS
staging area.


.. py:currentmodule:: tardis.tardis_portal.filters.exif

EXIF Metadata extraction
^^^^^^^^^^^^^^^^^^^^^^^^


.. autoclass:: EXIFFilter
   :members:
   :undoc-members:
