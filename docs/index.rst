.. MyTARDIS documentation master file, created by sphinx-quickstart on
   Fri Jul 3 10:23:35 2009. You can adapt this file completely to your
   liking, but it should at least contain the root `toctree`
   directive.

========
MyTARDIS
========

MyTARDIS is a multi-institutional collaborative venture that
facilitates the archiving and sharing of data and metadata collected
at major facilities such as the Australian Synchrotron and ANSTO and
within Institutions.

An example of the benefit of a system such a MyTARDIS in the protein
crystallography community is that while the model coordinates and
(less often) the structure factors (processed experimental data) are
stored in the community Protein Data Bank (PDB) the raw diffraction
data is often not available. There are several reasons why this is
important, which can be summarised as:

 * The availability of raw data is extremely useful for the
   development of improved methods of image analysis and data
   processing.
 * Fostering the archival of raw data at an institutional level is one
   the best ways of ensuring that this data is not lost (laboratory
   archives are typically volatile).

Homepage
========

You can get a copy of MyTardis from http://github.com/mytardis/mytardis

The latest documentation can be found on http://mytardis.readthedocs.org

For installation instructions see :doc:`install`.

Contents
========

User Documentation
------------------

.. toctree::
   :maxdepth: 2

   overview

   userguide

   searching
   tabs

Administration
--------------

.. toctree::
   :maxdepth: 2

   install
   admin
   schemaparamsets
   ingesting

   ref/auth_framework
   ref/filters
   ref/app_oaipmh
   ref/app_migration

Development
-----------

.. toctree::
   :maxdepth: 2

   architecture
   data

   contextual_views

   changes
   contributing

   Source Code Documentation <pydoc/modules>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

