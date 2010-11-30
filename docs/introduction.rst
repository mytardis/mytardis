======
TARDIS
======

TARDIS is a multi-institutional collaborative venture that facilitates the archiving and sharing of data and metadata collected at major facilities such as the Australian Synchrotron and ANSTO and within Institutions.

An example of the benefit of a system such as TARDIS in the protein crystallography community is that while the model coordinates and (less often) the structure factors (processed experimental data) are stored in the community Protein Data Bank (PDB) the raw diffraction data is often not available. There are several reasons why this is important, which can be summarised as:

 * The availability of raw data is extremely useful for the development of improved methods of image analysis and data processing.
 * Fostering the archival of raw data at an institutional level is one the best ways of ensuring that this data is not lost (laboratory archives are typically volatile).

Download
--------

You can get a copy of TARDIS from http://code.google.com/p/mytardis/

===========
Quick Start
===========

Prerequisites
-------------

Redhat::

   sudo yum install cyrus-sasl-ldap cyrus-sasl-devel openldap-devel libxslt libxslt-devel libxslt-python

Debian/Ubuntu::

   sudo apt-get install libsasl2-dev libldap libldap2-dev libxslt1.1 libxslt1-dev python-libxslt1

Building
--------

TARDIS is using the buildout buildsystem to handle dependencies and create teh python class path::

   python bootstrap.py
   ./bin/buildout

TARDIS can now be executed in it's simplist form using::

   ./bin/django-admin.py runserver

This will execute django using the builtin SQLite DBMS and only be accessable on *localhost*.


.. seealso::

   http://www.buildout.org
      The Buildout homepage.


