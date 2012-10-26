=============
Migration App
=============

The migration app supports the orderly migration of data files between different storage locations under the control of a single MyTardis instance.

The initial version of the app simply provides a django-admin command for manually migrating the data associated with a Datafile, Dataset or Experiment.  This will evolve to the point where the migration can be run on a schedule, and the selection of files for migration is based on tailorable criteria, and is aware of storage availability.

Setup
=====

Add the migration application to the INSTALLED_APPS list in your MyTardis project's settings file

.. code-block:: python

    INSTALLED_APPS += (
        TARDIS_APP_ROOT + '.migration',
    )

Describe the available destinations for transferring files to.  Each destination is a dictionary in the list, and the 'name' attribute gives its name::

    MIGRATION_DESTINATIONS = [{'name': 'test', 
                               'transfer_type': 'http',
                               'datafile_protocol': '',
                               'trust_length': False,
                               'metadata_supported': True,
                               'base_url': 'http://127.0.0.1:4272/data/'}]

(TODO - describe the other attributes.)

Specify the default migration destination.  If none is specified, the "--dest" option becomes mandatory for the "migrate" command::

    DEFAULT_MIGRATION_DESTINATION = 'test'

List the migration transfer provider classes.  Currently we only implement one provider, but adding custom providers should not be difficult::

    MIGRATION_PROVIDERS = {'http': 'tardis.apps.migration.SimpleHttpTransfer'}


Commands
========

The initial version of the migration app provides the "migrate" command to perform migrations

Usage
~~~~~
``./bin/django-admin migrate datafile | datafiles <id> ...``
``./bin/django-admin migrate dataset | datasets <id> ...``
``./bin/django-admin migrate experiment | experiments <id> ...``
``./bin/django-admin migrate destinations``

.. option:: -d DESTINATION, --dest=DESTINATION
.. option:: -v, --verbose

The first form migrates the files associated with one or more DataFiles.  The migration of a single file is atomic.  If the migration succeeds, the Datafile metadata in MyTardis will have been updated to the new location.  If it fails, the metadata will not be altered.  The migration process also takes steps to ensure that the file has been correctly transferred.  The final step of a migration is to delete the original copy of the file.  This is currently not performed atomically.

The second and third forms migrate all Datafiles in the respective Datasets or Experiments.  These operations are atomic at the level of a single Datafile, as above.

The final form of the command lists the transfer destinations that the app has been configured with.   

Architecture
============

TBD

Implementation
==============

Currently, only Datafiles that are local and verified can be migrated.  The reason for the latter is that we depend on the file matching its checksums when we check that the file has been migrated correctly.

When a file is migrated, the Datafile is changed as follows:

 * The 'url' field is set to the url of the file at the destination.
 * The 'protocol' field is set to the 'datafile_protocol' attribute in the destination descriptor.
 * The 'filename' field is cleared.

We currently support two ways of checking that a file has been transferred correctly.  The preferred way is to get the transfer destination to calculate and return the metadata (checksums and length) for its copy of the file.  If that fails (or is not supported), the fallback is to read back the file from the destination and do the checksumming locally.

Normally, we require there to be either an MD5 or SHA512 checksum in the metadata.  However if 'trust_length' is set, we will accept matching file lengths as being sufficient to verify the transfer.  That would normally be a bad idea, but if the transfer process is sufficiently reliable, file length checking may be sufficient.  (In this mode, a transfer provider could get away with sending a HEAD request and using the "Content-length".)
