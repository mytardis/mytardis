=========
Ingesting
=========

MyTARDIS supports 2 different XML schemas for importing data. One
method is METS and the other is using a MyTARDIS specific XML
format. METS is the preferred format because it is supported by
systems other that MyTARDIS so will provide more versatility in the
long run.


METS
----

The Meta-data Encoding and Transmission Standard was recommended by
Monash Librarians and ANU in 2008 as the XML description format for
MyTARDIS datasets.


MyTARDIS XML
------------

The MyTARDIS XML format matches to the data model that is being used
within MyTARDIS so it provides a truer mapping between the XML elements
and MyTARDIS.::

   <experiment>
           <title>Specialist Crystallography at the Australian Synchrotron</title>
           <createdate>2007-10-30T00:00:00+11:00</createdate>
           <lastmoddate>2007-10-30T00:00:00+11:00</lastmoddate>
           <abstract>We aim to detemine the crystal structures of several micro-crystalline materials and compare the data quality with that obtained recently for the SCrAPS program at the ChemMatCars beamline.</abstract>
           <organization>Australian Synchrotron</organization>
           <creator>VBL MetaMan</creator>
           <author>Dr. Paul Jensen</author>
           <author>Dr. Peter Turner</author>
           <dataset>
                   <description>Australian Synchrotron Proposal ID: 286</description>
                   <file>
                           <name>OKxtal1_1_001.img</name>
                           <size>8389120</size>
                           <md5>unknown</md5>
                           <path>file://Frames/test/OKxtal1_1_001.img</path>
                           <metadata schema="...">
                                   ... (custom metadata here)
                           </metadata>
                   </file>
           </dataset>
   </experiment>


Ingestion Script
----------------

Ingesting files can be trough the web using a POST request.


Simple ingestion script::

   #!/bin/bash

   file="$1"
   username="localdb_admin"
   password="secret"
   host="http://localhost:8000"
   owner="$username"

   curl -F username=$username -F password=$password -F xmldata=@${file} -F experiment_owner=$owner "$host/experiment/register/"

To use this script simple paste it into a new file called
*register.sh* and `chmod +x register.sh` then you can call it using
`./register.sh file.xml` there are several example XML and METS files
within the tardis tests.


.. seealso::

   http://www.loc.gov/standards/mets/
      Metadata Encoding and Tranmission Standard
