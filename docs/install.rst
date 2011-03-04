=======
Install
=======

Prerequisites
-------------

Redhat::

   sudo yum install cyrus-sasl-ldap cyrus-sasl-devel openldap-devel libxslt libxslt-devel libxslt-python

Debian/Ubuntu::

   sudo apt-get install libssl-dev libsasl2-dev libldap-2.4-2 libldap2-dev libxslt1.1 libxslt1-dev python-libxslt1

Configuration
-------------

Configuring MyTARDIS is done through a standard Django *settings.py*
file there are some extra config options that are specific to MyTARDIS.

.. attribute:: tardis.settings_changeme.FILE_STORE_PATH

   The location of the file store.


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

.. attribute:: tardis.settings_changeme.LDAP_ENABLED

   Boolean that enables LDAP support.

.. attribute:: tardis.settings_changeme.LDAP_URL

   LDAP the DNS name of your LDAP directory, for example
   *directory.example.com*


.. attribute:: tardis.settings_changeme.BASE_DN

   The DN Base of the LDAP server.


Repository
~~~~~~~~~~

.. attribute:: tardis.settings_changeme.FILE_STORE_PATH

   The path to the MyTARDIS repository. This i where files will be
   copied to once they are ingested into the system.

.. attribute:: tardis.settings_changeme.STAGING_PATH

   The path to the staging path. This is where new files to be
   included in datasets will be sourced.



.. seealso::

   http://www.buildout.org
      The Buildout homepage.
