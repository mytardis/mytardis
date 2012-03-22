===================
Installing MyTARDIS
===================

The sections through to Extended Configuration below provide a Quick Start guide for getting a basic MyTARDIS installation up and running.  The following section provides additional information on advanced configuration and add-on capabilities of MyTARDIS.

Prerequisites
-------------

Redhat::

   sudo yum install cyrus-sasl-ldap cyrus-sasl-devel openldap-devel libxslt libxslt-devel libxslt-python git

Debian/Ubuntu::

   sudo apt-get install subversion python python-dev libpq-dev libssl-dev libsasl2-dev libldap2-dev libxslt1.1 libxslt1-dev python-libxslt1 libexiv2-dev git

Download
--------

To get the current master branch::

   git clone git://github.com/mytardis/mytardis.git
   cd mytardis

This clones the repository as read-only.

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

Single Search
~~~~~~~~~~~~~

Instructions on installing and configuring Solr for advanced search are available from :doc:`searchsetup`.

Additional Tabs
~~~~~~~~~~~~~~~

Additional and custom tabs may be configured in MyTARDIS on a per-installation basis.  The tabs are implemented as separate Django applications with a single view (index), listed in the TARDIS_APPS configuration item and either linked to, or installed in the TARDS_APP_ROOT directory, by default ``tardis/apps``.

Documentation on the additional tabs is available from :doc:`tabs`.


Deployment
----------

Collecting Static Files
~~~~~~~~~~~~~~~~~~~~~~~

For performance reasons you should avoid static files being served via the
application, and instead serve them directly through the webserver.

To collect all the static files to a single directory::

   ./bin/django collectstatic


.. attribute:: tardis.settings_changeme.STATIC_ROOT

   This contains the location to deposit static content for serving.


.. attribute:: tardis.settings_changeme.STATIC_URL

   The path static content will be served from. (eg. ``/static`` or
   ``http://mytardis-resources.example.com/``)

.. seealso::

   `collectstatic <https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#collectstatic>`_,
   `STATIC_ROOT <https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-STATIC_ROOT>`_,
   `STATIC_URL <https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-STATIC_URL>`_

.. _apache-wsgi:

Serving with Apache HTTPD + mod_wsgi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See `./apache` for example configurations.

Serving with Nginx + uWSGI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this configuration, Nginx serves static files and proxies application
requests to a uWSGI server::

       HTTP  +-----------+ uWSGI +--------------+
    +------->|   Nginx   +------>| uWSGI Server |
             +-----------+       +--------------+
               0.0.0.0:80         127.0.0.1:3031

Unlike :ref:`apache-wsgi`, application requests run in a completely different
process to web requests. This allows the application server to be run as a
seperate user to the web server, which can improve security.

This configuration allows more flexibility when tuning for performance, but
does add additional deployment complexity.

MyTardis comes with a Foreman_ Profile, suitable for starting a server or
exporting system scripts:

.. code-block:: bash

    # Install Foreman (requires rubygems)
    sudo gem install foreman
    # Start with Foreman
    foreman start
    # Export Upstart start-up scripts (running as user "django")
    # (We use a patched template while we wait for
    # https://github.com/ddollar/foreman/pull/137 to be merged.)
    sudo foreman export upstart /etc/init -u <mytardis_user> -p 3031 -t ./foreman


Nginx should then be configured to send requests to the server::

    server {
        listen 80 default;
        listen 443 default ssl;
        client_max_body_size 4G;
        keepalive_timeout 5;

        root /home/django/public;

        location / {
            include uwsgi_params;
            uwsgi_pass 127.0.0.1:3031;
        }

        location /static/ {
            alias /home/django/mytardis/static/;
        }

    }

Don't forget to create the static files directory and give it appropriate
permissions.

.. code-block:: bash

    # Collect static files to /home/django/mytardis/static/
    bin/django collectstatic
    # Allow Nginx read permissions
    setfacl -R -m user:nginx:rx static/

.. seealso::
            `Django with uWSGI`_

.. _Foreman: http://ddollar.github.com/foreman/
.. _`Django with uWSGI`: https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/uwsgi/
