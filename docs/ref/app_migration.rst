=============
Migration App
=============

The migration app supports the orderly migration of data files between
different storage locations under the control of a single MyTardis instance.
The secondary storage locations are essentially "dumb" consisting in the
simple case of nothing more than an off-the-shelf WebDAV server.

The initial version of the app simply provides a django admin command for
manually migrating the data associated with a Datafile, Dataset or Experiment.

TO DO:

 * Provide a framework that allows migrations to be run on a schedule, and the
   selection of files for migration is based on tailorable criteria, and is
   aware of storage availability.

 * Once the datafile has migrated, the default behaviour of MyTardis when the
   user attempts to fetch / view the Datafile is to fetch back a temporary
   copy.  Arrange that the temporary copy can be cached and/or reinstated
   locally.  Arrange that the files can be retrieved directly from the
   secondary store to the user's web browser.  (The last would involve some
   kind of SSO involving MyTardis and the secondary store's web server.)

 * Provide some indication to end users that datafiles have been migrated and
   that access will be slower.

 * Provide some mechanism for end users to influence which files are migrated,
   or not.

 * Work needs to be done on configuration of the destinations and providers
   ... so configuration details are liable to change.

Setup
=====

Add the migration application to the INSTALLED_APPS list in your MyTardis
project's settings file

.. code-block:: python

    INSTALLED_APPS += (
        TARDIS_APP_ROOT + '.migration',
    )

Specify the default migration destination.  This should be the name of a
Location.  If none is specified, the "--dest" option becomes mandatory for the
"migrate" command::

    DEFAULT_DESTINATION = 'test'

Finally, you need to specify the tuning parameters for the "scoring" formula
used to decide what files to migrate; for example::

    MIGRATION_SCORING_PARAMS = {
         'user_priority_weighting': [5.0, 2.0, 1.0, 0.5, 0.2],
         'file_size_threshold': 0,
         'file_size_weighting': 1.0,
         'file_access_threshold': 0,
         'file_access_weighting': 0.0,
         'file_age_threshold': 0,
         'file_age_weighting': 0.0}

The base formula is as follows::

    score = datafile_score * dataset_weighting

    datafile_score = size_score + age_score + access_score

    size_score = if log10(size) > file_size_threshold:
                     (log10(size) - file_size_threshold) * file_size_weighting
 		 else:
                     0.0

    age_score = if age > file_age_threshold:
                    (age - file_age_threshold) * file_age_weighting
	        else:
	            0.0

    access_score = if access > file_access_threshold:
                      (access - file_access_threshold) * file_access_weighting
	           else:
	              0.0

    dataset_weighting = Max-over-experiments(experiment_weighting)

    experiment_weighting = Max-over-owners(user_weighting)

    user_weighting = user_priority_weighting[user.priority])

where the file size is measured in bytes, and the access and age times are
measured in days since the last access or update based on file system
timestamps.

(The example above has weightings of zero for the file age and access, so
scoring will only take account of file sizes.)

Security Considerations
=======================

We recommend that the target server for a migration destination should be
locked down, and that all access and updates to the base URL should limitted
to a site specific admin account.

We recommend that the target server use HTTP Digest rather than HTTP Basic
authentication to provide minimum protection for the admin credentials.

If there is a significant risk of network snooping, etc, consider using
SSL/TLS for the transfers.


Commands
========

The initial version of the migration app provides the "migratefiles" command
to perform migrations

Usage
~~~~~
``./bin/django migratefiles migrate [<type> <id> ...]``
``./bin/django migratefiles mirror [<type> <id> ...]``
``./bin/django migratefiles ensure <amount>``
``./bin/django migratefiles reclaim <amount>``
``./bin/django migratefiles score``
``./bin/django migratefiles destinations``

.. option:: -d DESTINATION, --dest=DESTINATION
.. option:: --verbosity={0,1,2,3}
.. option:: -n, --dryRun
.. option:: --noRemove
.. option:: -a, --all

The 'migrate' subcommand migrates the files associated with one or more
DataFiles, DataSets or Experiments.  The "<type>" is one of "dataset",
"datasets", "datafile", "datafiles", "experiment" or "experiments", and "<id>
..." is a sequence of object ids for objects of the target type.
Alternatively, the "--all" option selects all Datafiles for migration.

Datafiles are migrated from a "source" location to a "destination" location.
The default "source" location is "local" (i.e. the MyTardis primary
filestore), and the default "destination" location is site specific.

The migration of a single file is atomic.  If the migration succeeds, the
Datafile metadata in MyTardis will have been updated to the new location.  If
it fails, the metadata will not be altered.  The migration process also takes
steps to ensure that the file has been correctly transferred.  The final step
of a migration is to delete the original copy of the file.  This is currently
not performed atomically.

The 'mirror' subcommand form just copies the files to the destination.  It is
equivalent to a 'migrate' without the database update and without the local
file removal.

The 'reclaim' subcommand attempts to reclaim "<amount>" bytes of local disc
space by migrating files.  Files are selected for migration by scoring them
using the configured scoring algorithm and parameters.  We then choose files
with the highest scores.  The "<amount>" argument should be a number (>= zero)
followed by an optional scale factor; e.g. "1.1k" means 1.1 multiplied by 1024
and truncated.  Scaling factors "k", "m", "g" and "t" are supported.

The 'ensure' subcommand is like 'reclaim', but the "<amount>" argument is
interpretted as the target amount of free space to maintain on the local file
system.

(As currently implemented, "reclaim" and "ensure" only support "local" as the
source location.  The issue is that we don't yet have a mechanism for
determining how much free space is available on locations other than "local".)

The 'score' subcommand simply scores all of the local files and lists their
details in descending score order.

The 'destinations' subcommand lists the configured transfer destinations.

The options are as follows:

  * -d, --dest=Location selects the target location for the migrate, mirror
    and reclaim subcommands.
  * -s, --source=Location selects the source location for the migrate, mirror
    and reclaim subcommands.  The default is "local".
  * --all used with migrate and mirror to select all Datafiles for the action.
  * -v, --verbosity=0,1,2,3 controls how much output the command produces.
  * --dryRun lists the files that would be migrated, mirrored or restored, but
    does not change anything.  (Currently, it doesn't check to see if the
    migrate / restore / mrror actions would have worked.)
  * --noRemove used with "migrate" to stop the removal of the file at the
    source location.  (This is implied in the case of mirroring.)
  * --help prints 'migratefiles' command help.

Architecture
============

TBD

Implementation
==============

By default, only Datafile replicas that are marked as verified can be
migrated.  We depend on the file matching its checksums after copying as a
check that the file has been migrated correctly.

The process for migration is roughly as follows:

 * Check that no Replica exists at the target location for the Datafile.
 * Check that the source Replica exists and is verified.
 * Prepare a new Replica descriptor:
   * generate the 'url' using the transfer provider's generate_url method
   * set 'protocol' to empty
   * set 'stay_remote' according to where target location is remote
   * set 'verified' to False.
 * Use the transfer provider's put_file method to transfer the data.
 * Check that the file transferred correctly: see below
 * Mark the new Replica as verified and save the record
 * If we are doing a "migrate"
   * Delete the source Replica record
   * Use the source transfer provider's remove_file method to remove the
     file ... unless we are running in 'noRemove' mode.

We currently support two ways of checking that a file has been transferred
correctly.  The preferred way is to get the transfer destination to calculate
and return the metadata (checksums and length) for its copy of the file.  If
that fails (or is not supported), the fallback is to read back the file from
the destination and do the checksumming locally.

Normally, we require there to be either an MD5 or SHA512 checksum in the
metadata.  However if 'trust_length' is set, we will accept matching file
lengths as being sufficient to verify the transfer.  That would normally be a
bad idea, but if the transfer process is sufficiently reliable, file length
checking may be sufficient.  (In this mode, a transfer provider could get away
with sending a HEAD request and using the "Content-length".)

(Note that migrating and restoring are now symmetric, and there is no longer a
distinct 'restore' action.)
