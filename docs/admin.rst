====================
Database Maintenance
====================

Initialising
------------

When creating a new database the ``syncdb`` command will need to be
called to initialise the schema and insert the initial data fixtures.

Usage
~~~~~
``./bin/django syncdb --noinput``

Migrating
---------

Some of the upgrades to MyTARDIS will require that the database schema
be upgraded to match the internal data model. This tool migrates data
from old database schemas to the current one. It detects which version
of the database you are currently running and will automatically
migrate to the current version. If you decided not to use South for
migrating the data models and have removed it from the list of
INSTALLED_APPS in the settings.py file, you could skip this step and
go on initiating an administrator account with Django createsuperuser
which is described in more detail below.

In certain cases it is also necessary to update the permissions table.

Usage
~~~~~
``./bin/django migrate``

``./bin/django update_permissions``

creating superuser
---------
After success of database initialization or migration, please use a
command line utility called ``createsuperuser`` to create an
administrator account using the admin site which is hooked to the URL
/admin/.

Usage
~~~~~
``./bin/django createsuperuser``

backup
------

The backupdb command allows to backup and to restore of the MyTARDIS
database.  The command uses the corresponding database tool to
facilitate this task. Currently implemented are PostgreSQL and
MySQL. In case of backup, a directory called ``backups`` is created
(if it does not exists) in the working directory.  In case of restore,
the database for storing the tablespace must already exist before
loading the backup file into the database.

Usage
~~~~~
``./bin/django backupdb``

.. option:: -r FILE, --restore=FILE
.. option:: -v VERBOSITY, --verbosity=VERBOSITY
.. option:: --settings=SETTINGS
.. option:: --pythonpath=PYTHONPATH
.. option:: --traceback
.. option:: --version
.. option:: -h, --help
