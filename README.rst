README for MyTARDIS
===================

MyTARDIS is a multi-institutional collaborative venture that facilitates the
archiving and sharing of data and metadata collected at major facilities such
as the Australian Synchrotron and ANSTO and within Institutions.

An example of the benefit of a system such as MyTARDIS in the protein
crystallography community is that while the model coordinates and (less often)
the structure factors (processed experimental data) are stored in the
community Protein Data Bank (PDB) the raw diffraction data is often not
available. There are several reasons why this is important, which can be
summarised as:

-  The availability of raw data is extremely useful for the development
   of improved methods of image analysis and data processing.

-  Fostering the archival of raw data at an institutional level is one
   the best ways of ensuring that this data is not lost (laboratory
   archives are typically volatile).


Releases
--------

The `master` branch is the current stable release with all the latest bugfixes
included. It will move to newer versions automatically. Follow this branch
if you want to stay up to date in a production environment.

Each version has its own branch named by version number. At the time of
writing this is `3.5`. Follow this branch for your production installation and
perform version upgradres manually.

Each bugfix or set of fixes bumps the minor version and each new release is
tagged, eg. `3.5.2`. Use tagged releases if you are paranoid about changes to
the code you have not tested yourself.

To follow development, please see the contributing section below.

Reporting Bugs
--------------

Bug reports and feature requests can be made via our `public issue tracker`_.

.. _`public issue tracker`: https://github.com/mytardis/mytardis/issues

Contributing
------------

The `develop` branch is the cutting edge code base that all development is
based upon.

Send wishes, comments, etc. to tardis-devel@googlegroups.com.

New contributors are welcome, however all developers should review the
`pull-request checklist`_ before making pull requests.

.. _`pull-request checklist`: https://github.com/mytardis/mytardis/blob/master/CONTRIBUTING.rst


Code Health Status
------------------

.. image:: https://semaphoreapp.com/api/v1/projects/08628202-28c8-4c67-86bf-eccd88a9828e/345537/shields_badge.svg
   :target: https://semaphoreapp.com/grischa/mytardis
   :alt: Semaphore build status
