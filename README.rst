MyTardis
========

.. image:: https://readthedocs.org/projects/mytardis/badge/?version=develop
   :target: http://mytardis.readthedocs.org/en/develop/?badge=develop
   :alt: Documentation Status


.. image:: https://semaphoreapp.com/api/v1/projects/5d21cc89-645b-4793-bd78-cf525a0dcce2/345561/shields_badge.svg
   :target: https://semaphoreapp.com/mytardis/mytardis
   :alt: Semaphore build status

.. image:: https://www.codacy.com/project/badge/c5899f09f2c545edaaf6d474e9e5e11e
   :target: https://www.codacy.com/public/grischa/mytardis
   :alt: Codacy Badge

.. image:: https://coveralls.io/repos/mytardis/mytardis/badge.svg?branch=develop
  :target: https://coveralls.io/r/mytardis/mytardis?branch=develop
  :alt: Coveralls Badge

MyTardis is a multi-institutional collaborative venture that facilitates the
archiving and sharing of data and metadata collected at major facilities such
as the Australian Synchrotron and ANSTO and within Institutions.

An example of the benefit of a system such as MyTardis in the protein
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

Demo
----

To try out MyTardis, install Docker and run

.. code-block:: bash

   git clone https://github.com/mytardis/mytardis.git
   cd mytardis
   docker-compose up

This will download pre-built images from Docker Hub and start a complete
MyTardis service in your Docker host.

Open the web interface in your browser: http://localhost:8080 and
log in with username ``demo`` and password ``demo``.

Find out more
-------------

Project homepage http://mytardis.org

The source code is hosted at https://github.com/mytardis/mytardis

Documentation at http://mytardis.readthedocs.org includes

- User documentation
- Administrator documentation
- Developer documentation

Releases
--------

The default branch on GitHub is ``develop``. This is the cutting edge
development version. Please DO NOT use this in production, as it may have bugs
that eat your data.

The ``master`` branch is the current stable release with all the latest bugfixes
included. It will move to newer versions automatically. Follow this branch
if you want to stay up to date in a production environment.

Each version has its own branch named by version number. At the time of
writing this is ``3.7``. Follow this branch for your production installation and
perform version upgradres manually.

Each bugfix or set of fixes bumps the minor version and each new release is
tagged, eg. ``3.7.2``. Use tagged releases if you are paranoid about changes to
the code you have not tested yourself.

To follow development, please see the contributing section below.


Reporting Bugs
--------------

Bug reports and feature requests can be made via our `public issue tracker`_.

.. _`public issue tracker`: https://github.com/mytardis/mytardis/issues


Contributing
------------

New contributors are always welcome, however all developers should review the
`pull-request checklist`_ before making pull requests.

For any wishes, comments, praise etc. either open a GitHub issue or contact us.

Active developers are also welcome to join our Slack team.

Contact details can be found on `mytardis.org`_.

.. _`mytardis.org`: http://mytardis.org
.. _`pull-request checklist`: https://github.com/mytardis/mytardis/blob/master/CONTRIBUTING.rst
