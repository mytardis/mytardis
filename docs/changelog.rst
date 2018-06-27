Releases
========

4.0-prerelease
--------------
* Django 1.11
* Improved test coverage
* Continuous Integration tests run against Ubuntu 16.04 (MyTardis v3.x used 14.04)
    TO DO: Switch to Ubuntu 18.04 before v4.0 is released.
* ChromeDriver is used for BDD (Behaviour Driven Development) tests


3.9
---


3.8
---
* Refactored settings
* Added pagination to My Data view
* BDD tests using behave and phantomjs
* Added download MD5 checksum buttons to Dataset View
* Add `autocaching` task that allows data from a StorageBox to be cached to
  another StorageBox
* Re-wrote user documentation and switched to hosting docs on RTD
* Switched to using NPM to manage JS deps.
* Facility and instrument are now visible on Experiment and dataset views -
  thanks @avrljk
* Added setting that allows datasets ordered by id on the Experiment page.
* Added setting to make sha512 checksums optional.

3.7 - 17 March 2016
-------------------

* DataFile size is now a BigInteger field
* New settings for customisations, contextual view overrides (eg INDEX_VIEWS).
* A new AbstractTardisAppConfig class that all new tardis apps should subclass
* Third-party tardis app dependency checking
* Removed database index from Parameter.string_value to allow longer strings in
  Postgres. Migrations add a Postgres partial index for string_values shorter
  than 256 characters.
* Changed constraints on the instrument model; facility and instrument name are
  now unique together
* changed method tasks to task functions, pre-empting the removal of methods
  tasks in new celery versions
* RESTful API now supports ordering, e.g. &order_by=-title, for Experiments,
  Datasets and DataFiles.
* Allowed groups to be 'owners' of an Experiment. Enforce rule in views
  for web UI requiring every Experiment to have at least one user owner.
* Registration support updated for latest django-registration-redux package
* Speed-ups for dataset view page loading for datasets with large numbers of
  images.  The carousel is now limited to a maximum of 100 preview images.
* Reorganised and updated documentation


3.6 - 16 March 2015
-------------------

* removed legacy operations files (foreman, apache, uwsgi, etc)
* moved CI from Travis CI to Semaphore app
* removed buildout build system and setup.py dependency management
* build instructions in build.sh, using requirements.txt for dependencies now
* gunicorn instead of uwsgi
* updated Django to version 1.6.10
* removed migrations app
* renamed ``Dataset_File`` to ``DataFile``
* ``DataFile`` have a ``deleted`` and a ``version`` flag, for upcoming support
  of these features.
* verifying files does not have side-effects anymore
* renamed ``Author_Experiment`` to ``ExperimentAuthor``
* an ``ExperimentAuthor`` can now have an email and or a URL
* recoded ``Replica`` and ``Location`` as ``DataFileObject`` with associated
  ``StorageBox``, based on the Django File API
* API v1 got some additions, largely or fully backwards-compatible
* a publication workflow app, guided publication of data
* download data via SFTP using a built-in SFTP server
* removed most traces of METS
* AAF authentication support
* parameters that can store a generic foreign key (link to any database
  object)
* new models ``Instrument`` and ``Facility``
* basic support for SquashFS archives as ``StorageBox``. Probably requires
  installation-specific code such as what is used at the `Australian
  Synchrotron <https://github.com/grischa/synch-squash-parser>`_.
* error pages are no normal-sized
* new view "Facility Overview", for facility administrators to have overview
  over data.
* "MyData" includes owned and shared data
* safely allowing HTML in descriptions now. Achieved by "bleaching" of tags
* stats page faster through DB-server-side aggregation
* layout improvements
* pep8 and pylint improvements
* bug fixes

3.5 - 26 August 2013
--------------------

* REST API
* REST API keys
* Authorisation now supports object-level permissions
* Front page overview
* Contextual views for Datafiles, Datasets and Experiments
* Backwards incompatible database changes
* Replica multi file location support
* Migration of replicas
* Streaming downloads
* Django 1.5
* REDIS option for celery queue
* auto-verify files
* provisional directory support
* Pylint testing on Travis CI
* Some error pages are now functional
* optionally upload comfortably with Filepicker.io
* Experiment view page load speedup
* Removed ancient XML ingest format.

3.0 - unreleased
----------------

* Twitter Bootstrap
* javascript templates
* backbone.js rendering of datasets
* UI for transferring datasets
* bpython shell
* celery queue


2.0 - Unreleased
----------------
* Auth/Auth redesign [Gerson, Uli, Russel]

  * Authorisation. Support for several pluggable authorisation plugins
    (Django internal, LDAP, VBL). The added AuthService middleware
    provides a mechanism to query all available auth modules to
    determine what group memberships a users has.

  * Alternative authorisation. Rule based experiment access control
    engine was implemented with the following access attributes for
    indivdual users and groups: canRead, canWrite, canDelete,
    isOwner. Additionally, a time stamp can be specified for each
    access rule.

    Further information can be found at the wiki: `Authorisation
    Engine design
    <http://code.google.com/p/mytardis/wiki/AuthorisationEngineAlt>`_

* Metadata Editing [Steve, Grischa]
* New METS parser & METS exporter [Gerson]
* Dist/Buildout infrastructure [Russell]
* Through the web creation and editing of experiments [Steve, Russell]
* Through the web upload of files [Steve]
* Download protocol handler [Russel, Uli]
* Logging framework [Uli]
* Django 1.3


1.07 - 01/06/2010
-----------------

* Publish to tardis.edu.au interface created, though not implemented,
  pending legal text


1.06 - 15/03/2010
-----------------
* Parameter import interface for creation of new parameter/schema
  definitions
* iPhone Interface


1.05 - 01/03/2010
-----------------

* Images as parameters supported
* Data / metadata transfer from synchrotron is now 'threaded' using
  asynchronous web service transfers.


1.0 - 01/02/2010
----------------

* MyTardis created from existin MyTardis python / django codebase
* Allows private data to be stored
* Open key/value parameter model, replacing current crystallography
  one
* Internal data store for data
* LDAP Login
* Pagination of files
* Creation of synchrotron-tardis from MyTardis codebase including
  specific code for the VBL login service and data transfer to
  MyTardis deployments.
* Web server changed to apache and mod_wsgi


0.5 - 2009
----------

* Re-wrote federated index (python / django)
* Federated stores are now simple web server based with optional FTP
  access
* Runs on Jython / Tomcat


0.1 - 2007
----------

* Federated index (php) running on Apache HTTP Server
* Crystallography data deposition and packaging tools for Fedora
  Commons (java swing desktop)
* Search Interface via web
