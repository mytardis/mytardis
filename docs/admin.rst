====================
Database Maintenance
====================

initialising
------------

When creating a new database the ``syncdb`` command will need to be
called to initialise the schema and instert the initial data fixtures.

Usage
~~~~~
``./bin/django syncdb``

migrating
---------

Some of the upgrades to MyTARDIS will require that the database schema
be upgraded to match the internal datamodel. This tool migrates data
from old database schemas to the current one. It detects which version
of the database you are currently running and will automatically
migrate to the current version.

Usage
~~~~~
``./bin/django migrate``


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
