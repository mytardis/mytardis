=======================================================
BACKUPDB - Database backup for the Django Web framework
=======================================================

SYNOPSIS
--------
``django-admin.py backupdb``

.. option:: -r FILE, --restore=FILE
.. option:: -v VERBOSITY, --verbosity=VERBOSITY
.. option:: --settings=SETTINGS
.. option:: --pythonpath=PYTHONPATH
.. option:: --traceback
.. option:: --version
.. option:: -h, --help


DESCRIPTION
-----------

The backupdb command allows to backup and to restore of the Tardis
database.  The command uses the corresponding database tool to
facilitate this task. Currently implemented are PostgreSQL and
MySQL. In case of backup, a directory called ``backups`` is created
(if it does not exists) in the working directory.  In case of restore,
the database for storing the tablespace must already exist before
loading the backup file into the database.


ENVIRONMENT
-----------

``DJANGO_SETTINGS_MODULE``

This environment variable defines the settings module to be read.  It
should be in Python-import form, e.g. "tardis.settings". Only
necessary when backup.py is called directly, e.g. without the
django-admin.py command.


SEE ALSO
--------

The django-admin.py documentation:
http://docs.djangoproject.com/en/1.2/ref/django-admin/


AUTHORS/CREDITS
---------------

Modified version of a Django Snippet originally posted at
http://djangosnippets.org/snippets/823/


LICENSE
-------
For the full license text refer to the COPYING.txt file in the
Tardis distribution.
