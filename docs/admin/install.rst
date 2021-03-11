============
Installation
============

The sections through to Extended Configuration below provide a Quick Start
guide for getting a basic MyTardis installation up and running. The following
section provides additional information on advanced configuration and add-on
capabilities of MyTardis.


Prerequisites
-------------

Ubuntu (18.04 LTS is recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Login as ``ubuntu`` user, not root.

Run this script for Python 3::

   sudo bash install-ubuntu-py3-requirements.sh

It will install required packages with these commands:

.. literalinclude:: ../../install-ubuntu-py3-requirements.sh
   :language: bash


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

If you want to use ``virtualenvwrapper``, you can install it with
``sudo pip3 install virtualenvwrapper`` and set the
``export VIRTUALENV_PYTHON=/usr/bin/python3`` in your ``~/.bashrc`` or
``~/.profile`` to ensure that ``mkvirtualenv`` will make a Python 3
virtual environment.  For more information on configuring
``virtualenvwrapper``, see https://virtualenvwrapper.readthedocs.io/en/latest/install.html#shell-startup-file

To activate ``virtualenvwrapper``:

For Ubuntu 18.04 with Python 3 (using pip3 installed virtualenvwrapper)::

  source /usr/local/bin/virtualenvwrapper.sh

Then create the ``mytardis`` virtual environment::

  mkvirtualenv mytardis

Note: the next time you want to work with this virtualenv, run the appropriate
``source`` command and then use the command: ``workon mytardis``

Make sure you are running Python 3.x::

  $ python -V
  Python 3.6.9

Now upgrade pip and setup tools::

  pip install -U pip setuptools

Check pip version::

  $ pip -V
  pip 21.0.1 from /home/ubuntu/mytardis/mytardis/lib/python3.6/site-packages/pip (python 3.6)

MyTardis dependencies are then installed with pip::

  pip install -U -r requirements.txt

To install minimal Javascript dependencies for production::

  npm install --production

To install Javascript dependencies for production and for testing::

  npm install && npm test

To compile Webpack assets::

  npm run-script build

Configuring MyTardis is done through a standard Django *settings.py*
file. MyTardis comes with a set of default settings in its
``tardis/default_settings/`` package. You can import this as the basis
of your own config file - options defined here will override the
relevant options in ``default_settings/*.py``.

Create a new file ``tardis/settings.py`` containing the following::

  from .default_settings import *

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

  python -c "import os; from random import choice; key_line = '%sSECRET_KEY=\"%s\"  # generated from build.sh\n' % ('from .default_settings import * \n\n' if not os.path.isfile('tardis/settings.py') else '', ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789@#%^&*(-_=+)') for i in range(50)])); f=open('tardis/settings.py', 'a+'); f.write(key_line); f.close()"


This is the minimum set of changes required to successfully run the
server in development mode. You can make any other site-specific changes
as necessary.


Initialisation
--------------

Create and configure the database::

  python manage.py migrate
  python manage.py createcachetable default_cache
  python manage.py createcachetable celery_lock_cache

This avoids creating a superuser before the MyTardis specific ``UserProfile``
table has been created. More information about the ``migrate``
commands can be found at :doc:`../admin`.

Next, create a superuser::

  python manage.py createsuperuser

MyTardis can now be executed in its simplest form using::

  python manage.py runserver

This will start the Django web server at http://localhost:8000/.


Running in a Docker Container
-----------------------------

Installation steps from above can be summarised as a following `Dockerfile`:

.. literalinclude:: ../../Dockerfile
   :language: text

**This is a minimum configuration for MyTardis, which is not suitable for running
in production.**

To build and run Docker container locally you will need to run following commands::

  docker build . --tag mytardis
  docker run --name mytardis -p 8000:8000 mytardis

Alternatively you can use pre-built Docker image from DockerHub::

  docker run --name mytardis -p 8000:8000 mytardis/mytardis:develop

If you are keep in MyTardis development, we recommended you to
visit https://github.com/mytardis/mytardis-dev for a full stack
development environment, which runs using Docker.

Extended configuration
----------------------

See below for some extra configuration options that are specific to MyTardis.

An automatically generated documentation of the settings can be found in
:doc:`../pydoc/tardis`.


Essential Production Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These settings are essential if you want to run MyTardis in production mode
(``DEBUG = False``).

.. attribute:: SECRET_KEY

   This key needs to be unique per installation and, as the name implies,
   be kept secret.

   A new one can be conveniently generated with the command::

     echo "SECRET_KEY='`python manage.py generate_secret_key`'" >> tardis/settings.py

However, the more complex command shown above needs to be used at installation
time.

.. attribute:: ALLOWED_HOSTS

   ``ALLOWED_HOSTS`` is a list of hostnames and/or IP addresses under which the
   server is accessible. If this is not set you will get a 500 Error for any
   request.

Database
~~~~~~~~

.. attribute:: tardis.default_settings.DATABASE_ENGINE

   The database server engine that will be used to store the MyTardis
   metadata, possible values are *postgresql_psycopg2*, *postgresql*,
   *mysql*, *sqlite3* or *oracle*.

.. attribute:: tardis.default_settings.DATABASE_NAME

   The name of the database to used to store the data, this is the
   path to the database if you are using the SQLite storage engine.

.. attribute:: tardis.default_settings.DATABASE_USER

   The user name used to authenticate to the database. If you are
   using SQLite this field is not used.

.. attribute:: tardis.default_settings.DATABASE_PASSWORD

   The password used to authenticate to the database. If you are using
   SQLite this field is not used.

.. attribute:: tardis.default_settings.DATABASE_HOST

   The host name of the machine hosting the database service. If this
   is empty then localhost will be used. If you are using SQLite then
   this field is ignored.

.. attribute:: tardis.default_settings.DATABASE_PORT

   The port the database is running on. If this is empty then the
   default port for the database engine will be used. If you are using
   SQLite then this field is ignored.


LDAP
~~~~

For further information see :ref:`LDAP authentication<ref-ldap_auth>`


Repository
~~~~~~~~~~

.. attribute:: tardis.default_settings.DEFAULT_STORAGE_BASE_DIR

   The path to the default MyTardis storage location. This is where files will
   be stored to if you do not provide any other location explicitly through
   ``StorageBox``es.

.. attribute:: tardis.default_settings.REQUIRE_DATAFILE_CHECKSUMS

   If True, a Datafile requires an MD5 or SHA-512 checksum from the time
   it is first recorded in the MyTardis database.  This enables a model-level
   constraint check each time a Datafile record is saved.  Defaults to True.
   Datafile record is saved.

.. attribute:: tardis.default_settings.REQUIRE_DATAFILE_SIZES

   If True, a Datafile require a size from the time it is first recorded in
   the MyTardis database.  This enables a model-level
   constraint check each time a Datafile record is saved.  Defaults to True.

.. attribute:: tardis.default_settings.REQUIRE_VALIDATION_ON_INGESTION

   If True, ingestion of a Datafile is only permitted if the Datafile
   matches its supplied size and/or checksums.  Defaults to True.


Access Rights & Licensing
~~~~~~~~~~~~~~~~~~~~~~~~~

Licences
^^^^^^^^

By default, the Creative Commons Attribution 4.0 International licences are loaded.

You can use the admin interface to add other licences. Please ensure
``allows_distribution`` is set to the correct value to ensure the licence
appears in conjunction with suitable public access types.


Legal Notice
^^^^^^^^^^^^

When changing the public access rights or licence for an experiment, a
legal notice is displayed. You can override it by
specifying following settings in *settings.py*:

.. code-block:: python

   LEGAL_TEXT = "A sample legal Text"



Filters
~~~~~~~

.. attribute:: tardis.default_settings.POST_SAVE_FILTERS

   This contains a list of post save filters that are execute when a
   new data file is created.

   The **POST_SAVE_FILTERS** variable is specified like::

      POST_SAVE_FILTERS = [
          ("tardis.tardis_portal.filters.exif.EXIFFilter", ["EXIF", "http://exif.schema"]),
          ]

   For further details please see the :ref:`ref-filterframework` section.


Archive Organizations
~~~~~~~~~~~~~~~~~~~~~

.. attribute:: tardis.default_settings.DEFAULT_ARCHIVE_FORMATS.

   This is a prioritized list of download archive formats to be used
   in contexts where only one choice is offered to the user; e.g. the
   "download selected" buttons.  (The list allows for using different
   archive formats depending on the user's platform.)

.. attribute:: tardis.default_settings.DEFAULT_PATH_MAPPER.

   This gives the default archive "organization" to be used.
   Organizations are defined via the next attribute.

.. attribute:: tardis.default_settings.DOWNLOAD_PATH_MAPPERS.

   This is a hash that maps archive organization names to Datafile filename
   mapper functions.  These functions are reponsible for generating the
   archive pathnames used for files written to "tar" and "zip" archives
   by the downloads module.

   The **DOWNLOAD_PATH_MAPPERS** variable is specified like::

       DOWNLOAD_PATH_MAPPERS = {
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


Storage Locations ( ``StorageBox`` es)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A MyTardis instance can be configured to support multiple locations
( ``StorageBox`` es) for storing data files.  Each location holds copies
( ``DataFileObject`` s) of ``DataFile`` s that are recorded in the MyTardis
database.

The ``StorageBox`` architecture is compatible with the `Django File Storage API`_. This makes it relatively easy to support a number of different
storage backends such as cloud storage or SFTP servers.  Please refer to the
:doc:`StorageBox documentation<storage>` for more detailed information.


Single Search
~~~~~~~~~~~~~

Instructions on installing and configuring Elasticsearch for advanced search
are available from :doc:`searchsetup`.


Additional Tabs
~~~~~~~~~~~~~~~

Additional and custom tabs may be configured in MyTardis on a per-installation
basis.  The tabs are implemented as separate Django applications with a single
view (index), listed in the TARDIS_APPS configuration item and either linked
to, or installed in the TARDIS_APP_ROOT directory, by default ``tardis/apps``.

Documentation on the additional tabs is available from :doc:`../apps/contextual_views`.

Additional Views
~~~~~~~~~~~~~~~~

Custom views may be configured in MyTardis on a per-installation basis.  The
tabs are implemented as separate Django applications with a single view
function listed in the ``*_VIEWS`` configuration item and added to the
``INSTALLED_APPS`` list.

Refer to the :doc:`views documentation<../apps/contextual_views>` for further information.

Site Customisations
~~~~~~~~~~~~~~~~~~~

Some settings that allow customised messages and styles.

.. code-block:: python

    PUBLICATION_INTRODUCTION = """
    <p><strong>... introduction and publication agreement ...</strong></p>
    """
    SITE_STYLES = ''  # should be CSS

    # if either GA setting is empty, GA is disabled
    GOOGLE_ANALYTICS_ID = ''  # whatever Google provides
    GOOGLE_ANALYTICS_HOST = ''  # the host registered with Google

    # these refer to any template finder findable location, e.g. APPDIR/templates/...
    CUSTOM_ABOUT_SECTION_TEMPLATE = 'tardis_portal/about_include.html'
    CUSTOM_USER_GUIDE = 'user_guide/index.html'


Deployment
----------

Collecting Static Files
~~~~~~~~~~~~~~~~~~~~~~~

For performance reasons you should avoid static files being served via the
application, and instead serve them directly through the webserver.

To collect all the static files to a single directory::

  python manage.py collectstatic


.. attribute:: tardis.default_settings.STATIC_ROOT

   This contains the location to deposit static content for serving.


.. attribute:: tardis.default_settings.STATIC_URL

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
      ssl_protocols TLSv1.1 TLSv1.2;
      ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:DES-CBC3-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA';
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
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_set_header Host $http_host;
          proxy_redirect off;
          proxy_pass http://mytardis;
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

The ``X-Forwarded-Proto`` header is explained in http://docs.gunicorn.org/en/stable/deploy.html#id5:

  It is recommended to pass protocol information to Gunicorn. Many web
  frameworks use this information to generate URLs. Without this information,
  the application may mistakenly generate ‘http’ URLs in ‘https’ responses,
  leading to mixed content warnings or broken applications.

To tell MyTardis to set this header in its HTTP requests and redirects, you'll
need the following in your ``settings.py``::

  SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

For more information, including warnings on the risks of misconfiguring this setting,
see: https://docs.djangoproject.com/en/2.2/ref/settings/#secure-proxy-ssl-header

Don't forget to create the static files directory and give it appropriate
permissions. The location is set in the ``settings.py`` file.

.. code-block:: bash

   # Collect static files to ``settings.STATIC_ROOT``
   python manage.py collectstatic
   # Allow Nginx read permissions
   setfacl -R -m user:nginx:rx static_dir

.. seealso::
            `Django with Gunicorn`_

.. _`Django with Gunicorn`: https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/gunicorn/

.. _`Django File Storage API`: https://docs.djangoproject.com/en/dev/ref/files/storage/

Serving with Apache HTTPD + mod_wsgi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We do not support the use of Apache. If you need this and want to support this
use case, we welcome your contribution of any relevant documentation.

Creating Systemd Services for Gunicorn and Celery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Gunicorn is a Python WSGI HTTP Server which is suitable for production (when
combined with NGINX).  Gunicorn is typically run from a Systemd service
(on Ubuntu 16.04 or Ubuntu 18.04), saved in
`/etc/systemd/system/gunicorn.service`::

    [Unit]
    Description=gunicorn daemon
    After=network.target

    [Service]
    User=mytardis
    Group=mytardis
    WorkingDirectory=/home/mytardis/mytardis
    ExecStart=/home/mytardis/.virtualenvs/mytardis/bin/gunicorn \
      -c gunicorn_settings.py -b unix:/tmp/gunicorn.socket \
      -b 127.0.0.1:8000 \
      --log-syslog \
      wsgi:application

    [Install]
    WantedBy=multi-user.target

On older systems (Ubuntu 14.04), Supervisor can be used instead of Systemd.
In this case, the Gunicorn service would be configured in
`/etc/supervisor/conf.d/gunicorn.conf`::

    [program:gunicorn]
    command=/home/mytardis/.virtualenvs/mytardis/bin/gunicorn
     -c /home/mytardis/mytardis/gunicorn_settings.py
     -b unix:/tmp/gunicorn.socket
     -b 127.0.0.1:8000
     --log-syslog
     wsgi:application
    user=mytardis
    stdout_logfile=/var/log/gunicorn.log
    redirect_stderr=true

A single server MyTardis deployment requires only one Gunicorn service,
but MyTardis can be installed on multiple web nodes, each running NGINX
and Gunicorn to accomodate load balancing and high availability using
HAProxy.

The Celery workers which run MyTardis asynchronous tasks also require a
service configuration, which is typically implemented with Systemd (on
Ubuntu 16.04 or Ubuntu 18.04), saved in
`/etc/systemd/system/celeryworker.service`::

    [Unit]
    Description=celeryworker daemon
    After=network.target

    [Service]
    User=mytardis
    Group=mytardis
    WorkingDirectory=/home/mytardis/mytardis
    Environment=DJANGO_SETTINGS_MODULE=tardis.settings
    ExecStart=/home/mytardis/.virtualenvs/mytardis/bin/celery worker \
      -A tardis.celery.tardis_app \
      -c 2 -Q celery,default -n "allqueues.%%h"

    [Install]
    WantedBy=multi-user.target

On older systems (Ubuntu 14.04), Supervisor can be used instead of Systemd.
In this case, the Celery worker service would be configured in
`/etc/supervisor/conf.d/celeryworker.conf`::

    [program:celeryd]
    environment=
      DJANGO_SETTINGS_MODULE=tardis.settings
    command=/home/mytardis/.virtualenvs/mytardis/bin/celery worker
      -A tardis.celery.tardis_app
      -c 2 -Q celery,default -n "allqueues.%%h"
    user=mytardis
    directory=/home/mytardis/mytardis
    stdout_logfile=/var/log/celeryd.log
    redirect_stderr=true
    killasgroup=true
    stopwaitsecs=600

For tasks scheduled by Celerybeat, the Systemd service configuration
(for Ubuntu 16.04 or Ubuntu 18.04), is saved in
`/etc/systemd/system/celerybeat.service`::

    [Unit]
    Description=celerybeat daemon
    After=network.target

    [Service]
    User=mytardis
    Group=mytardis
    WorkingDirectory=/home/mytardis/mytardis
    Environment=DJANGO_SETTINGS_MODULE=tardis.settings
    ExecStart=/home/mytardis/.virtualenvs/mytardis/bin/celery beat \
      -A tardis.celery.tardis_app --loglevel INFO

    [Install]
    WantedBy=multi-user.target

On older systems (Ubuntu 14.04), Supervisor can be used instead of Systemd.
In this case, the Celerybeat service would be configured in
`/etc/supervisor/conf.d/celerybeat.conf`::

    [program:celerybeat]
    environment=
      DJANGO_SETTINGS_MODULE=tardis.settings
    command=/home/mytardis/.virtualenvs/mytardis/bin/celery beat
      -A tardis.celery.tardis_app --loglevel INFO
    user=mytardis
    directory=/home/mytardis/mytardis
    stdout_logfile=/var/log/celerybeat.log
    redirect_stderr=true
