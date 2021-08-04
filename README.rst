MyTardis
========

.. image:: https://readthedocs.org/projects/mytardis/badge/?version=develop
   :target: http://mytardis.readthedocs.org/en/develop/?badge=develop
   :alt: Documentation Status

.. image:: https://semaphoreci.com/api/v1/mytardis/mytardis/branches/develop/badge.svg
   :target: https://semaphoreci.com/mytardis/mytardis
   :alt: Semaphore build status

.. image:: https://travis-ci.org/mytardis/mytardis.svg?branch=develop
    :target: https://travis-ci.org/mytardis/mytardis
    :alt: Travis CI build status
   
.. image:: https://api.codacy.com/project/badge/Grade/c27bad18abaf443c93e58192757c2025
   :alt: Codacy Badge
   :target: https://app.codacy.com/app/mytardis/mytardis?utm_source=github.com&utm_medium=referral&utm_content=mytardis/mytardis&utm_campaign=badger
   
.. image:: https://coveralls.io/repos/mytardis/mytardis/badge.svg?branch=develop
  :target: https://coveralls.io/r/mytardis/mytardis?branch=develop
  :alt: Coveralls Badge
  
.. image:: https://codecov.io/gh/mytardis/mytardis/branch/develop/graph/badge.svg
  :alt: Codecov Badge
  :target: https://codecov.io/gh/mytardis/mytardis

Overview
--------
MyTardis began at Monash University to solve the problem of users needing to
store large datasets and share them with collaborators online. Its particular
focus is on integration with scientific instruments, instrument facilities and
research storage and computing infrastructure; to address the challenges of data
storage, data access, collaboration and data publication.

`Read more... <http://www.mytardis.org/about/>`_

Key features for users
----------------------
The MyTardis data management platform is a software solution that manages research data and the associated metadata. MyTardis handles the underlying storage to ensure that data is securely archived and provides access to the data through a web portal. Data hosted in MyTardis can also be accessed via SFTP.

`Read more... <http://www.mytardis.org/introduction/>`_

Key features for instrument facilities
--------------------------------------
MyTardis takes care of distributing data to your users. Its instrument integration technology takes care of securely and automatically shifting data from instrument to repository and makes it accessible by the right users.

`Read more... <http://www.mytardis.org/for-facilities/>`_

Developing for MyTardis
-----------------------
MyTardis is mostly written in the `Python programming language <https://www.python.org/>`_ and is built on top of the `Django web framework <https://www.djangoproject.com/>`_. A complete installation of the service also includes an `Elasticsearch <https://www.elastic.co/>`_ index, a `RabbitMQ <https://www.rabbitmq.com/>`_-based task queue, an `Nginx <http://nginx.org/>`_ server, and a `PostgreSQL <http://www.postgresql.org/>`_ database.

To set up and manage these services we employ the `Kubernetes <https://kubernetes.io/>`_ orchestration software and cloud technologies.

`Read more... <http://www.mytardis.org/for-developers/>`_

Find out more
-------------

Project homepage http://mytardis.org

The source code is hosted at https://github.com/mytardis/mytardis

Documentation at http://mytardis.readthedocs.org includes

- User documentation
- Administrator documentation
- Developer documentation

The wiki at https://github.com/mytardis/mytardis/wiki includes

- Links to MyTardis add-ons, including apps and post-save filters
- Information about MyTardis community events

Known deployments
-----------------
- **Store.Synchrotron**: https://store.synchrotron.org.au/
- **Store.Monash**: https://store.erc.monash.edu
- **NIF ImageTrove**: https://imagetrove.cai.uq.edu.au/
- **MHTP Medical Genomics**: https://mhtp-seq.erc.monash.edu/
- **ANSTO**: https://tardis.nbi.ansto.gov.au/
- **Monash MyTardis Demo**: https://mytardisdemo.erc.monash.edu/

Related projects and repositories
---------------------------------
- **MyData**: https://github.com/mytardis/mydata

  - A desktop application for managing uploads to MyTardis
- **NIF ImageTrove**: https://github.com/NIF-au/imagetrove

  - A tool for ingesting and archiving NIF datasets, including

    - Web front end: `MyTardis <http://mytardis.org/>`_
    - A DICOM server: `DICOM ToolKit <http://dicom.offis.de/dcmtk.php.en>`_
    - A dataset uploader: `imagetrove-uploader <https://github.com/NIF-au/imagetrove-uploader>`_
    - Federated authentication with the Australian Access Federation's `Rapid Connect <https://rapid.aaf.edu.au>`_ service
- **NIF ImageTrove Docker deployment**: https://github.com/UWA-FoS/docker-mytardis

  - For ease of deployment, all of ImageTrove's components are packaged into a Docker container.
- **NIF Trusted Data Repositories**: https://github.com/NIF-au/TDR

  - Delivering durable, reliable, high-quality image data

Releases
--------

The default branch on GitHub is ``develop``. This is the cutting edge
development version. Please DO NOT use this in production, as it may have bugs
that eat your data.

The ``master`` branch is the current stable release with all the latest bug fixes
included. It will move to newer versions automatically. Follow this branch
if you want to stay up to date in a production environment.

Each version has its own branch named by version number. At the time of
writing, the latest release is ``4.5.0``, tagged from the ``series-4.5``
branch. Follow this branch for your production installation and
perform version upgrades manually.

Each bug fix or set of fixes bumps the minor version and each new release is
tagged, eg. ``4.5.1``. Use tagged releases if you are paranoid about changes to
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
