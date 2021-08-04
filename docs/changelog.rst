Releases
========

4.6.0
-----
* #3091 Unable approve Google auth user
* #3089 Events log update (switch to a native JSONField)
* #3028 and #3029 Security fixes as per CodeQL advice
* #3014 Track HSM app recalls with events log
* Dependency updates

4.5.0
-----
* Support for displaying online/offline files status for file in HSM
* Support for requesting recall of an offline dataset
* Support for requesting recall of an offline datafile
* Updated various Python and JS libraries
* Bugfixes
  - Fixed #2901
  - PushTo related fixes #2910
  - Fix redirect to next page
  - Fixes related to tree view #2742

4.4.0
-----
* User activity logging app
* Updated various Python and JS libraries
* Fix to Google Chrome installation
* Bugfixes
  - add SSH key

4.3.0
-----
* Updated various Python and JS libraries
* Removed Mustache and Backbone JS libraries (replaced with React)
* No new session will be created on API call or health check
* Check DataFile permissions in API differently (performance gain)
* Check for dataset permissions during API calls (security bug)
* New uploader registration email to be send to managers group not admins

4.2.0
-----
* Upgraded Django from 1.11.26 to 2.2.6
* Upgraded Bootstrap from 3.4.1 to 4.1.3
* Continuous Integration testing implemented for Python 3.5, 3.6, 3.7 and 3.8
* Dropped support for Python 2
* Dataset view now has a tree-based file browser
* Added a task which can be scheduled to clean up unverified files
* Added a task which can be scheduled to clean up DataFiles without DataFileObjects
* Bug fixes
  - Ensured thumbnail image files are opened in binary format, required for Python 3
  - Fixed bug with downloads on Python 3 by removing use of .__next__()
  - Fixed bugs in Push To's encoding/decoding of SSH certificates in Python 3
  - Fixed bug in MyTardis SFTP service relating to use of gevent with Django 2.2
* Dependency updates
  - Python and JS dependencies have been updated to address vulnerabilities.

4.1.5
-----
* Update AngularJS to address the SNYK-JS-ANGULAR-534884 vulnerability.
* Update the handlebars version in package-lock.json to avoid having
  "npm install" report high severity vulnerabilities.
* Fix the dataset metadata API test which was failing on Python 3.5.

4.1.4
-----
* Fixed duplicate form submission bugs for create experiment/dataset
* Fixed search bug which restricted instrument drop-down to 20 records
* Fixed some byte string encoding issues with LDAP auth in Python 3
* Fixed Python 3.5 unit tests
* Fixed pickled StorageBoxOption values for Python 3

4.1.3
-----
* Update the https-proxy-agent version in package-lock.json to avoid having
  "npm install" display "found 1 high severity vulnerability".

4.1.2
-----
* Allow .jsx files to be included in assets/js/tardis_portal/ and ensure that
  they won't be linted using the jQuery ESLint configuration
* Switch back to the official version of the pyoai dependency

4.1.1
-----
* Fix Python 3 bug with string encoding in deep download mapper
  which affected directory names in SFTP interface.

4.1
---
* Added React search components and django-elasticsearch-dsl backend
* Removed post-save filters middleware, replaced with microservice architecture
* Added RabbitMQ task priorities support, dropped support for Redis as a broker
* Upgraded Bootstrap CSS framework from v2.3.2 to v3.4.1
* Added Python 3 support
* Added webpack to collect static assets (JS / CSS), supporting ES6, JSX etc.
* Annotated storage box related tasks with their storage box name, visible
  in "celery inspect active"
* Added task for clearing Django sessions
* Added timestamps (created and modified) in facility and instrument models
* Updated built-in Creative Commons licenses to v4
* Added django-storages and boto3 to requirements to support S3 storage boxes
  and storing static assets in S3
* Improved efficiency of checksums and downloads for files in S3 storage
* COMPUTE_SHA512 now defaults to False. COMPUTE_MD5 still defaults to True.
* Legal text for publishing can now be specified in settings
* Now using Dataset created_time in facility overview instead of experiment
  created time
* Added a new setting to prevent large datasets (many files) from being scanned
  for image files at page load time
* API v1's instrument resource now allows any authenticated user to list the
  instrument names, which is used in the new search interface
* The ExperimentAuthor model now exposed in API v1
* MyTardis no longer tries to guess an appropriate storage box for new
  DataFileObjects unless REUSE_DATASET_STORAGE_BOX is True
* Improved BDD test coverage, now measuring template coverage with
  django-coverage-plugin
* Bug fixes (GitHub Issue numbers below)
  - Fixed #1503
  - Fixed #1568
  - Removed bob@bobmail.com from default ADMINS, fixing #1613
  - Fixed #1664
  - Fixed #1708
  - Fixed #1857
  - Fixed #1853
  - Fixed concatenated messages issue in user sharing and group sharing dialogs
  - Fixed #1790
  - Fixed truncated TAR download issue with unverified files
  - Fixed sharing with AAF/Google issue
  - Fixed some broken Font Awesome icons

4.0.2
-----
* Upgraded Django to 1.11.23
* Upgraded vulnerable dependencies of JS dev dependencies
* Fixed #1844 (remove a hard-coded LDAP attribute)

4.0.1
-----
* Removed anzsrc_codes tardis app which contained a potentially insecure dependency (rdflib)
* Added created_time and modified_time fiels in the Instrument and Facility models
* Updated Python and Javascript dependencies which had vulnerabilities reported since the v4.0 release.
* Fixed token authentication (#1531, 615d9df)
* Fixed some Font Awesome icons (1ac549d)
* Fixed an incomplete database migration for the Dataset created_time field. This fix is included in the tardis/tardis_portal/migrations/0016_add_timestamps.py migration which also adds the created_time and modified_time fields to the Instrument and Facility models (ec238b4)
* Removed hard-coded LDAP attributes (#1664, 96a0fbf)
* Fixed issue with get_accessible_datafiles_for_user potentially returning an empty list instead of an empty QuerySet (a13cefc)
* Fixed issue with Add/Save Experiment Metadata - added a form attribute to the Save button. (fd2393a)
* In S3 storage documentation, removed reference to old fork of django-storages. (f0c62d5)
* Fixed issue where MyTardis could try to verify SHA512 sums even when COMPUTE_SHA512 was set to False (#1419, 1da1b3b)
* In S3 storage documentation, removed reference to old fork of django-storages. (f0c62d5)
* Fixed issue where MyTardis could try to verify SHA512 sums even when COMPUTE_SHA512 was set to False (#1419, 1da1b3b)
* Fixed issue where downloading a TAR of a dataset including unverified files could result in a "Truncated tar archive" error (#1425, b4fa17c)
* Fixed issue where MyTardis tried to retrieve thumbnail images for non-image files, resulting in 404 errors (e261065)
* Fixed issue where failing to set ADMINS in tardis/settings.py could cause MyTardis to attempt to send emails to bob@bobmail.com (#1613, f8ed6dd)
* Fixed issue where Facility Overview's "Load more" button was enabled while content was still loading. (a28a253)

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
