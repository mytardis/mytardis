===================
Installing MyTARDIS
===================

The sections through to Extended Configuration below provide a Quick Start
guide for getting a basic MyTARDIS installation up and running.  The following
section provides additional information on advanced configuration and add-on
capabilities of MyTARDIS.


Prerequisites
-------------

Ubuntu 14.04::

  apt-get update
  apt-get install python-pip git libxml2-dev libxslt1-dev python-dev \
  zlib1g-dev python-wand python-virtualenv virtualenvwrapper python-psycopg2 \
  python-yaml ipython python-anyjson python-bs4 python-billiard \
  python-feedparser python-html5lib python-httplib2 python-pystache \
  python-crypto python-flexmock python-dateutil

Redhat/CentOS::

  sudo yum install cyrus-sasl-ldap cyrus-sasl-devel openldap-devel libxslt \
  libxslt-devel libxslt-python git graphviz-devel


We do not actively develop or deploy on RedHat or CentOS, so the list of
required packages might be incomplete.

Depending on which flavour of RHEL or CentOS and which db try one of::

  sudo yum install libevent-devel

or::

  sudo yum install compat-libevent14-devel


Download
--------

To get the most recent stable release::

  git clone -b master https://github.com/mytardis/mytardis.git
  cd mytardis

This clones the repository as read-only.

Or, to get the current development branch::

  git clone -b develop git://github.com/mytardis/mytardis.git
  cd mytardis


Quick configuration
-------------------

It is recommended that you use a virtualenv. The list of packages above
includes the ``virtualenvwrapper`` toolkit. Set up your environment with these
commands::

  source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
  mkvirtualenv --system-site-packages mytardis
  pip install -U pip

Next time you want to work with this virtualenv, run::

  source /usr/share/virtualenvwrapper/virtualenvwrapper.sh  # or add this to .bash_profile
  workon mytardis

MyTARDIS dependencies are then installed with pip::

  pip install -r requirements.txt

Configuring MyTARDIS is done through a standard Django *settings.py*
file. MyTARDIS comes with a sample configuration file at
``tardis/settings_changeme.py``. You can import this as the basis of your own
config file - options defined here will override the relevant options in
``settings_changeme.py``.

Create a new file ``tardis/settings.py`` containing the following::

  from settings_changeme import *

  # Add site specific changes here.

  # Turn on django debug mode.
  DEBUG = True

  # Use the built-in SQLite database for testing.
  # The database needs to be named something other than "tardis" to avoid
  # a conflict with a directory of the same name.
  DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
  DATABASES['default']['NAME'] = 'tardis_db'

In addition you will need to create a new ``SECRET_KEY`` for your installation.
This is important for security reasons.

A convenient method is to run the following command in your mytardis
installation location::

  python -c "import os; from random import choice; key_line = '%sSECRET_KEY=\"%s\"  # generated from build.sh\n' % ('from tardis.settings_changeme import * \n\n' if not os.path.isfile('tardis/settings.py') else '', ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789\\!@#$%^&*(-_=+)') for i in range(50)])); f=open('tardis/settings.py', 'a+'); f.write(key_line); f.close()"


This is the minimum set of changes required to successfully run the
server. You can make any other site-specific changes as necessary.


Initialisation
--------------

Create and configure the database::

  python mytardis.py syncdb --all --noinput
  python mytardis.py migrate --fake

This avoids creating a superuser before the MyTardis specific ``UserProfile``
table has been created. More information about the ``syncdb`` and ``migrate``
commands can be found at :doc:`admin`.

Next, create a superuser::

  python mytardis.py createsuperuser

MyTARDIS can now be executed in its simplest form using::

  python mytardis.py runserver

This will start the Django web server at http://localhost:8000/.


Extended configuration
----------------------

See below for some extra configuration options that are specific to MyTARDIS.

An automatically generated documentation of the settings can be found in
:doc:`pydoc/tardis`.


Essential Production Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These settings are essential if you want to run MyTardis in production mode
(``DEBUG = False``).

.. attribute:: SECRET_KEY

   This key needs to be unique per installation and, as the name implies,
   be kept secret.

   A new one can be conveniently generated with the command::

     echo "SECRET_KEY='`python mytardis.py generate_secret_key`'" >> tardis/settings.py

However, the more complex command shown above needs to be used at installation
time.

.. attribute:: ALLOWED_HOSTS

   ``ALLOWED_HOSTS`` is a list of hostnames and/or IP addresses under which the
   server is accessible. If this is not set you will get a 500 Error for any
   request.

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

.. attribute:: tardis.settings_changeme.DEFAULT_STORAGE_BASE_DIR

   The path to the default MyTARDIS storage location. This is where files will
   be stored to if you do not provide any other location explicitly through
   ``StorageBox``es.

.. attribute:: tardis.settings_changeme.STAGING_PATH

   The path to the staging path. This is where new files to be
   included in datasets will be sourced. This functionality, however, is
   not available in current MyTardis versions.

.. attribute:: tardis.settings_changeme.REQUIRE_DATAFILE_CHECKSUMS

   If True, a Datafile requires an MD5 or SHA-512 checksum from the time
   it is first recorded in the MyTardis database.  This enables a model-level
   constraint check each time a Datafile record is saved.  Defaults to True.
   Datafile record is saved.

.. attribute:: tardis.settings_changeme.REQUIRE_DATAFILE_SIZES

   If True, a Datafile require a size from the time it is first recorded in
   the MyTardis database.  This enables a model-level
   constraint check each time a Datafile record is saved.  Defaults to True.

.. attribute:: tardis.settings_changeme.REQUIRE_VALIDATION_ON_INGESTION

   If True, ingestion of a Datafile is only permitted if the Datafile
   matches its supplied size and/or checksums.  Defaults to True.


Access Rights & Licensing
~~~~~~~~~~~~~~~~~~~~~~~~~

Licences
^^^^^^^^

By default, no licences are loaded. A user can make metadata public without
assigning a licence, but they cannot allow public access to their data.

Creative Commons licences (for Australia) are available in
``tardis/tardis_portal/fixtures/cc_licenses.json``. You can load them with
 ``python mytardis.py loaddata``.

You can use the admin interface to add other licences. Please ensure
``allows_distribution`` is set to the correct value to ensure the licence
appears in conjunction with suitable public access types.


Legal Notice
^^^^^^^^^^^^

When changing the public access rights or licence for an experiment, a
legal notice is displayed. You can override it by either:

#. creating a new app (probably your site theme) and putting your legal text in
   ``tardis/apps/<app_name>/static/publishing_legal.txt``, or
#. directly making changes to
   ``tardis/tardis_portal/static/publishing_legal.txt``.


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


Archive Organizations
~~~~~~~~~~~~~~~~~~~~~

.. attribute:: tardis.settings_changeme.DEFAULT_ARCHIVE_FORMATS.

   This is a prioritized list of download archive formats to be used
   in contexts where only one choice is offered to the user; e.g. the
   "download selected" buttons.  (The list allows for using different
   archive formats depending on the user's platform.)

.. attribute:: tardis.settings_changeme.DEFAULT_ARCHIVE_ORGANIZATION.

   This gives the default archive "organization" to be used.
   Organizations are defined via the next attribute.

.. attribute:: tardis.settings_changeme.ARCHIVE_FILE_MAPPERS.

   This is a hash that maps archive organization names to Datafile filename
   mapper functions.  These functions are reponsible for generating the
   archive pathnames used for files written to "tar" amd "zip" archives
   by the downloads module.

   The **ARCHIVE_FILE_MAPPERS** variable is specified like::

       ARCHIVE_FILE_MAPPERS = {
           'test': ('tardis.apps.example.ExampleMapper',),
           'test2': ('tardis.apps.example.ExampleMapper', {'foo': 1})
       }

   The key for each entry is the logical name for the organization, and
   the value is a tuple consisting of the function's pathname and a set
   of optional keyword arguments to be passed to the function.  At runtime,
   the function is called with each Datafile as a positional argument, and
   an additional 'rootdir' keyword argument.  The function should compute
   and return a (unique) pathname based on the Datafile and associated
   objects.  If the function returns **None**, this tells the archive builder
   to leave out the file.

   By default, the archive builder uses the built-in "deep-storage" mapper which
   gives pathnames that try to use directory information to rebuild a file tree.


Storage Locations (``StorageBox``es)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A MyTardis instance can be configured to support multiple locations
(``StorageBox``es) for storing data files.  Each location holds copies
(``DataFileObject``s) of ``DataFile``s that are recorded in the MyTardis
database.

The ``StorageBox`` architecture is compatible with the Django File Storage API
(TODO link). This makes it relatively easy to support a number of different
storage backends such as cloud storage or SFTP servers.  Please refer to the
:doc:`StorageBox documentation<storage>` for more detailed information.


Single Search
~~~~~~~~~~~~~

Instructions on installing and configuring Solr for advanced search are
available from :doc:`searchsetup`.


Additional Tabs
~~~~~~~~~~~~~~~

Additional and custom tabs may be configured in MyTARDIS on a per-installation
basis.  The tabs are implemented as separate Django applications with a single
view (index), listed in the TARDIS_APPS configuration item and either linked
to, or installed in the TARDS_APP_ROOT directory, by default ``tardis/apps``.

Documentation on the additional tabs is available from :doc:`tabs`.

Additional Views
~~~~~~~~~~~~~~~~

Custom views may be configured in MyTARDIS on a per-installation basis.  The
tabs are implemented as separate Django applications with a single view
function listed in the ``*_VIEWS`` configuration item and added to the
``INSTALLED_APPS`` list.

Refer to the :doc:`views documentation<contextual_views>` for further information.


Deployment
----------

Collecting Static Files
~~~~~~~~~~~~~~~~~~~~~~~

For performance reasons you should avoid static files being served via the
application, and instead serve them directly through the webserver.

To collect all the static files to a single directory::

  python mytardis.py collectstatic


.. attribute:: tardis.settings_changeme.STATIC_ROOT

   This contains the location to deposit static content for serving.


.. attribute:: tardis.settings_changeme.STATIC_URL

   The path static content will be served from. (eg. ``/static`` or
   ``http://mytardis-resources.example.com/``)

.. seealso::

   `collectstatic <https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#collectstatic>`_,
   `STATIC_ROOT <https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-STATIC_ROOT>`_,
   `STATIC_URL <https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-STATIC_URL>`_


Serving with Nginx + Gunicorn
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this configuration, Nginx serves static files and proxies application
requests to a Gunicorn server::

       HTTP  +-----------+       +-----------------+
    +------->|   Nginx   +------>| Gunicorn Server |
             +-----------+       +-----------------+
               0.0.0.0:80         127.0.0.1:8000


Nginx should then be configured to send requests to the server. Here is an
example configuration (SSL part from Mozilla SSL configurator). Please amend
for your own needs and understand the settings before deploying it.::

  upstream mytardis {
      server unix:/var/run/gunicorn/mytardis/socket;
      server 127.0.0.1:8000 backup;
  }
  server {
      listen 80 default_server;
      server_name demo.mytardis.org;
      return 301 https://$server_name$request_uri;
  }

  server {
      listen 443 default_server ssl;
      server_name demo.mytardis.org;

      # certs sent to the client in SERVER HELLO are concatenated in ssl_certificate
      ssl_certificate /path/to/signed_cert_plus_intermediates;
      ssl_certificate_key /path/to/private_key;
      ssl_session_timeout 5m;
      ssl_session_cache shared:SSL:50m;

      # Diffie-Hellman parameter for DHE ciphersuites, recommended 2048 bits
      ssl_dhparam /path/to/dhparam.pem;

      # intermediate configuration. tweak to your needs.
      ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
      ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:AES:CAMELLIA:DES-CBC3-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA';
      ssl_prefer_server_ciphers on;

      # HSTS (ngx_http_headers_module is required) (15768000 seconds = 6 months)
      add_header Strict-Transport-Security max-age=15768000;

      # OCSP Stapling ---
      # fetch OCSP records from URL in ssl_certificate and cache them
      ssl_stapling on;
      ssl_stapling_verify on;

      ## verify chain of trust of OCSP response using Root CA and Intermediate certs
      ssl_trusted_certificate /path/to/root_CA_cert_plus_intermediates;

      resolver <IP DNS resolver>;

      client_max_body_size 4G;
      keepalive_timeout 5;

      gzip off;  # security reasons
      gzip_proxied any;
      # MyTardis generates uncompressed archives, so compress them in transit
      gzip_types application/x-javascript text/css;
      gzip_min_length 1024;
      gzip_vary on;

      location / {
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Protocol $scheme;
          proxy_set_header Host $http_host;
          proxy_redirect off;
          proxy_pass http://mytardis;
          # this is to solve centos 6 error:
          # upstream prematurely closed
          client_max_body_size 4G;
          client_body_buffer_size 8192k;
          proxy_connect_timeout 2000;
          proxy_send_timeout 2000;
          proxy_read_timeout 2000;
      }

      location /static/ {
          expires 7d;
          alias /srv/static_files/;
      }
  }


Don't forget to create the static files directory and give it appropriate
permissions. The location is set in the ``settings.py`` file.

.. code-block:: bash

   # Collect static files to ``settings.STATIC_ROOT``
   python mytardis.py collectstatic
   # Allow Nginx read permissions
   setfacl -R -m user:nginx:rx static_dir

.. seealso::
            `Django with Gunicorn`_

.. _`Django with Gunicorn`: https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/gunicorn/


Serving with Apache HTTPD + mod_wsgi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We do not support the use of Apache. If you need this and want to support this
use case, we welcome your contribution of any relevant documentation.
