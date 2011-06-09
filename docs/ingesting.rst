=========
Ingesting
=========

There are three mechanisms for ingesting metadata and data into MyTARDIS:

#. User Interface
   The User Interface is appropriate for ingesting a single experiment by the end user with a relatively small amount of data.
#. Staging Area
   The Staging Area is appropriate for ingesting a single experiment by the end user with larger amounts of data.
#. Batch Ingestion
   Batch ingestion is typically used by facilities automatically ingesting all metadata from one or more instruments into MyTARDIS.

MyTARDIS supports 2 different XML schemas for importing metadata. One
method is METS and the other is using a MyTARDIS specific XML
format. METS is the preferred format because it is supported by
systems other that MyTARDIS so will provide more versatility in the
long run.


METS
----

The Meta-data Encoding and Transmission Standard was recommended by
Monash Librarians and ANU in 2008 as the XML description format for
MyTARDIS datasets.


Ingestion Script
----------------

Metadata may be easily ingested using a simple script and POST request::

   #!/bin/bash

   file="$1"
   username="localdb_admin"
   password="secret"
   host="http://localhost:8000"
   owner="$username"

   curl -F username=$username -F password=$password -F xmldata=@${file} -F experiment_owner=$owner "$host/experiment/register/"

To use this script paste it into a new file called, e.g.
*register.sh*, `chmod +x register.sh` then can call it using
`./register.sh file.xml`.  There are several example XML and METS files
within the tardis test suite.


Post Processing
---------------

MyTARDIS takes advantage of the Django signal framework to provide post
processing of files. The only default post processing step that is
enabled by default operates on newly created Dataset Files.


Staging Hook
^^^^^^^^^^^^

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


.. seealso::

   http://www.loc.gov/standards/mets/
      Metadata Encoding and Tranmission Standard
