Releases
========

4.1
---
* Bootstrap upgraded to v3.4.0
* Celery upgraded to v4.2.1
* RabbitMQ task priorities support, dropping support for Redis
* Storage box related tasks are annotated with the storage box name,
    visible in "celery inspect active".
* New Travis CI webhook to run Pylint with Python 3
* New task for clearing Django sessions
* New timestamps (created and modified) in facility and instrument models
* Fixed truncated TAR download issue with unverified files
* Fixed sharing with AAF/Google issue
* Fixed some broken Font Awesome icons
* Made autocache task more efficient.
* Some dependency updates:
    Update amqp from 2.3.2 to 2.4.1
    Update billiard from 3.5.0.4 to 3.5.0.5
    Update bleach from 2.1.4 to 3.1.0
    Update coverage from 4.5.1 to 4.5.2
    Update django from 1.11.16 to 1.11.20
    Update django-extensions from 1.8.1 to 2.5
    Update flexmock from 0.10.2 to 0.10.3
    Update gevent from 1.3.6 to 1.4.0
    Update gunicorn from 19.7.1 to 19.9.0
    Update kombu from 4.2.1 to 4.3.0
    Update lxml from 4.2.5 to 4.3.1
    Update mysqlclient from 1.3.13 to 1.4.2
    Update pillow from 5.2.0 to 5.4.1
    Update psycopg2-binary from 2.7.5 to 2.7.7
    Update pyjwt from 1.6.4 to 1.7.1
    Update pylint from 1.9.3 to 1.9.4
    Update python-dateutil from 2.7.5 to 2.8.0
    Update python-ldap from 2.4.27 to 3.1.0
    Update pytz from 2018.5 to 2018.9
    Update requests from 2.19.1 to 2.21.0
    Update selenium from 3.14.1 to 3.141.0
    Update six from 1.11.0 to 1.12.0
    Update social-auth-app-django from 3.0.0 to 3.1.0
    Update sphinx from 1.8.1 to 1.8.4
    Update sphinx-rtd-theme from 0.4.1 to 0.4.3
    Update urllib3 from 1.23 to 1.24.1
    Update wand from 0.4.4 to 0.5.0

4.0
---
* Django 1.11
* jQuery 3.3.1
* Improved test coverage
* Continuous Integration tests run against Ubuntu 18.04 (MyTardis v3.x used 14.04)
* ChromeDriver is used for BDD (Behaviour Driven Development) tests
* Social Auth, including AAF and Google Auth via OpenID Connect
* Migrating user accounts from LDAP or localdb to OpenID Connect
* Customizable user menu
* Using message.level_tag instead of message.tags in portal_template, so that
  extra tags can be added to Django messages without interfering with the Bootstrap
  alert class.
* My Data page (which previously contained Owned and Shared experiments) has been split
  into two pages - "My Data" and "Shared"
  - Each page loads thumbnails asynchronously for faster initial page load time
  - An improved pagination widget allows for a very large number of pages.
* Index page's thumbnails are loaded asynchronously for faster initial page load time.
* Login page can be replaced with a site-specific page
* SFTP can now be used with keys instead of passwords
* Upgraded Bootstrap from 2.0.4 to 2.3.2 (further upgrades coming soon)
* Fixed some bugs in single search
* jQuery code is being moved out of HTML templates and into JS files which can be linted (with ESLint) and tested (with QUnit).
* Removed old broken code and unnecessary code which is duplicated in other repositories.
   - Import via staging with jsTree
   - Uploadify
* Updated or removed (as appropriate) some out-of-date JS dependencies bundled within the MyTardis repository
   - Most JS dependences are installed by npm now, so we can run security checks with npm audit
* manage.py can now be used instead of mytardis.py and mytardis.py will soon be deprecated
* New support email setting can be used in email templates or HTML templates.
* Updating loadschemas management command for Django 1.11 and adding test for it
* Updated the dumpschemas management command for Django 1.11 and added a test for it
* Bug fixes (GitHub Issue numbers below)
    Fixed #243. Bug in tardis_acls.change_experiment permissions check
    Fixed #516 - only show "Add files" button if user has permission to upload files
    Fixed #636
    Fixed #637 - "()" is added to "Author" line every time an experiment is edited
    Fixed #779
    Fixed #868
    Fixed #893
    Fixed #988
    Fixed #1083
    Fixed #1185
* Added docs on X-Forwarded-Proto HTTP header for HTTPS deployments
* Added docs on configuring services in systemd or supervisor
* Removed password length restriction in linked user authentication form
* Removed settings_changeme - use default_settings instead
* Removed backslash from set of characters used to generate secret key.
* Removed django-celery - it is no longer necessary to run Celery via Django
* Improved forwards compatibility with Python 3, but we're not fully Python 3 compatible yet.
* Switched to PEP 328 relative imports
* Tests no longer require the unmaintained "compare" module
* Added a default value for DATA_UPLOAD_MAX_MEMORY_SIZE (required by Django 1.10+) to default settings
* Removed some unused dependencies, e.g. PyYAML
* Removed the createmysuperuser which is no longer needed
* Removed the checkhashes management command
* Removed the diffraction image filter
* Removed the backupdb management command
* Removed the old publication form - a new publication workflow is coming soon.

3.9
---
* Added deprecation warnings for functionality which will be removed in 4.0
* Added INTERNAL_IPS to default settings for template debugging on localhost
* Disabled the old publication forms app in default settings, and ensured
  that MyTardis didn't attempt to access its static content when disabled
* Removed apps code from ExperimentView's get_context_data which assumed
  that each app would provide a views module with an index
* Fixed a bug where creating a group which already existed gave a 500 error
* Fixed a bug where non-ASCII characters in experiment names could break SFTP
* Made dataset thumbnails optional - disabling them can improve page load times
* Fixed a bug which had made it difficult to delete a DataFileObject without
  a URI from the Django shell
* Fixed a bug which made search indexing fail when there were users with
  non-ASCII characters in their first or last name

3.8.1
-----
* Fix regression in Push To app

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
