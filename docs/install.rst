===================
Installing MyTARDIS
===================

Prerequisites
-------------

Redhat::

   sudo yum install cyrus-sasl-ldap cyrus-sasl-devel openldap-devel libxslt libxslt-devel libxslt-python

Debian/Ubuntu::

   sudo apt-get install subversion python python-dev libpq-dev libssl-dev libsasl2-dev libldap2-dev libxslt1.1 libxslt1-dev python-libxslt1 libexiv2-dev

Download
--------

To get the current trunk::

   svn co https://mytardis.googlecode.com/svn/trunk/ mytardis
   cd mytardis

Quick configuration
-------------------

MyTARDIS is using the Buildout build system to handle dependencies and create the python class path.

Configuring MyTARDIS is done through a standard Django *settings.py*
file. MyTARDIS comes with a sample configuration file at ``tardis/settings_changeme.py``. You can import this as the basis of your own config file - options defined here will override the relevant options in ``settings_changeme.py``.

Create a new file ``tardis/settings.py`` containing the following::

    from os import path
    from settings_changeme import *

    # Add site specific changes here.

    # Turn on django debug mode.
    DEBUG = True

    # Use the built-in SQLite database for testing.
    # The database needs to be named something other than "tardis" to avoid
    # a conflict with a directory of the same name.
    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
    DATABASES['default']['NAME'] = 'tardis_db'

Create a new file ``buildout-dev.cfg`` containing the following::

    [buildout]
    extends = buildout.cfg

    [django]
    settings = settings

.. note::
    The ``settings = settings`` line tells Buildout to use the settings
    file you just created.

This is the minimum set of changes required to successfully run the server. You can make any other site-specific changes as necessary.

Building
--------

Run the Buildout bootstrap script to initialise Buildout::

   python bootstrap.py

Download and build django and all dependencies::

   ./bin/buildout -c buildout-dev.cfg

This can be run again at any time to check for and download any new dependencies.

Create and configure the database::

    ./bin/django syncdb && ./bin/django migrate

Answer "no" when asked to create a superuser. More information about the ``syncdb`` and ``migrate`` commands can be found at :doc:`admin`.

Create a superuser::

    ./bin/django createsuperuser

This is deferred until after the migrate as the command has been overridden to set up MyTARDIS specific information.

MyTARDIS can now be executed in its simplest form using::

   ./bin/django runserver

This will start the Django web server at http://localhost:8000/.

Extended configuration
----------------------

See below for some extra configuration options that are specific to MyTARDIS.

Database
~~~~~~~~

.. attribute:: tardis.settings_changeme.DATABASE_ENGINE

   The database server engine that will be used to store the MyTARDIS
   metadata, possible values are *postgresql_psycopg2*, *postgresql*,
   *mysql*, *sqlite3* or *oracle*.

.. attribute:: tardis.settings_changeme.DATABASE_NAME

   The name of the database to used to store the data, this is the
   path to the database if you are using the SQLite storage engine.

.. attribute:: tardis.settings_changeme.DATABASE_USER

   The user name used to authenticate to the database. If you are
   using SQLite this field is not used.

.. attribute:: tardis.settings_changeme.DATABASE_PASSWORD

   The password used to authenticate to the database. If you are using
   SQLite this field is not used.

.. attribute:: tardis.settings_changeme.DATABASE_HOST

   The host name of the machine hosting the database service. If this
   is empty then localhost will be used. If you are using SQLite then
   this field is ignored.

.. attribute:: tardis.settings_changeme.DATABASE_PORT

   The port the database is running on. If this is empty then the
   default port for the database engine will be used. If you are using
   SQLite then this field is ignored.


LDAP
~~~~

For further information see :ref:`LDAP authentication<ref-ldap_auth>`


Repository
~~~~~~~~~~

.. attribute:: tardis.settings_changeme.FILE_STORE_PATH

   The path to the MyTARDIS repository. This is where files will be
   copied to once they are ingested into the system.

.. attribute:: tardis.settings_changeme.STAGING_PATH

   The path to the staging path. This is where new files to be
   included in datasets will be sourced.

Filters
~~~~~~~

.. attribute:: tardis.settings_changeme.POST_SAVE_FILTERS

   This contains a list of post save filters that are execute when a
   new data file is created.

   The **POST_SAVE_FILTERS** variable is specified like::

      POST_SAVE_FILTERS = [
          ("tardis.tardis_portal.filters.exif.EXIFFilter", ["EXIF", "http://exif.schema"]),
          ]

   For further details please see the :ref:`ref-filterframework` section.

.. seealso::

   http://www.buildout.org
      The Buildout homepage.
