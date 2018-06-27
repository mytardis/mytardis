Database
========


Initialising
------------

When creating a new database the ``migrate`` command will need to be
called to initialise the schema and insert the initial data fixtures.

Usage
~~~~~
``python manage.py migrate``

Migrating
---------

Some of the upgrades to MyTardis will require that the database schema
be upgraded to match the internal data model. The ``migrate`` command
migrates data from old database schemas to the current one. It detects
which version of the database you are currently running and will
automatically migrate to the current version. 

In certain cases it is also necessary to update the permissions table.

Usage
~~~~~
``python manage.py migrate``

If the model changes require it, run::

  python manage.py update_permissions


creating superuser
------------------

After success of database initialization or migration, please use a
command line utility called ``createsuperuser`` to create an
administrator account using the admin site which is hooked to the URL
/admin/.

Usage
~~~~~

``python manage.py createsuperuser``

Backup
------

Previous versions of MyTardis included a ``backupdb`` management command
but it has been removed in 4.0.  Please use the recommended backup tool
for your database engine, e.g. ``pg_dump`` or ``mysqldump``.
