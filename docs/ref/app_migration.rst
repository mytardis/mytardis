=============
Migration App
=============

The migration app supports the orderly migration of data files between different storage locations under the control of a single MyTardis instance.  The secondary storage locations are essentially "dumb" consisting in the simple case of nothing more than an off-the-shelf WebDAV server.

The app provides three django admin commands:

  * The "migratefiles" command can migrate (or mirror) data associated with manually selected Datafiles, Datasets or Experiments, or it can use a scoring system to select Datafiles for migration.

  * The "archive" command creates offline archives consisting of all of the data files for an Experiment and METS format "manifest" that includes all Experiment / Dataset / Datafile metadata.  Archives can be saved as local files, or saved via a transfer provider.  In the latter case, an record is added to the Archive table to facilitate later retrieval.

  * The "archivelist" command allows you to search and list the Archive table to identify previously created archives by user, experiment title, experiment id and/or date range.

TO DO:

 * Provide a framework that allows migrations to be run on a schedule, and the selection of files for migration is based on tailorable criteria, and is aware of storage availability.  (Meanwhile, cron jobs work.)

 * Once the datafile has migrated, the default behaviour of MyTardis when the user attempts to fetch / view the Datafile is to fetch back a temporary copy.  Arrange that the temporary copy can be cached and/or reinstated locally.  Arrange that the files can be retrieved directly from the secondary store to the user's web browser.  (The last would involve some kind of SSO involving MyTardis and the secondary store's web server.)

 * Provide some indication to end users that datafiles have been migrated and that access will be slower.

 * Provide some mechanism for end users to influence which files are migrated, or not.

 * Implement functionality for manual restoring archived experiments and/or on-demand fetching and restoring of datafiles. 

 * Work needs to be done on configuration of the destinations and providers ... so configuration details are liable to change.

Setup
=====

Add the migration application to the INSTALLED_APPS list in your MyTardis project's settings file

.. code-block:: python

    INSTALLED_APPS += (
        TARDIS_APP_ROOT + '.migration',
    )

Specify the default migration destination.  This should be the name of a Location.  If none is specified, the "--dest" option becomes mandatory for the "migrate" command::

    DEFAULT_DESTINATION = 'test'

Finally, you need to specify the tuning parameters for the "scoring" formula used to decide what files to migrate; for example::

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

where the file size is measured in bytes, and the access and age times are measured in days since the last access or update based on file system timestamps.

(The example above has weightings of zero for the file age and access, so scoring will only take account of file sizes.)

Security Considerations
=======================

We recommend that the target server for a migration destination should be locked down, and that all access and updates to the base URL should limitted to a site specific admin account.

We recommend that the target server use HTTP Digest rather than HTTP Basic authentication to provide minimum protection for the admin credentials.

If there is a significant risk of network snooping, etc, consider using SSL/TLS for the transfers. 


The "migratefiles" Command
==========================

The "migratefiles" command migrates or mirrors data files selected in various ways between different locations. 

Usage
~~~~~
``./bin/django migratefiles migrate [<type> <id> ...]``
``./bin/django migratefiles mirror [<type> <id> ...]``
``./bin/django migratefiles ensure <amount>``
``./bin/django migratefiles reclaim <amount>``
``./bin/django migratefiles score``
``./bin/django migratefiles destinations``

.. option:: -d LOCATION, --dest=LOCATION
.. option:: -s LOCATION, --source=LOCATION
.. option:: --verbosity={0,1,2,3}
.. option:: -n, --dryRun
.. option:: --noRemove
.. option:: -a, --all

Subcommands
~~~~~~~~~~~
The 'migrate' subcommand migrates the files associated with one or more DataFiles, DataSets or Experiments.  The "<type>" is one of "dataset", "datasets", "datafile", "datafiles", "experiment" or "experiments", and "<id> ..." is a sequence of object ids for objects of the target type.  Alternatively, the "--all" option selects all Datafiles for migration.

Datafiles are migrated from a "source" location to a "destination" location.  The default "source" location is "local" (i.e. the MyTardis primary filestore), and the default "destination" location is site specific.

The migration of a single file is atomic.  If the migration succeeds, the Datafile metadata in MyTardis will have been updated to the new location.  If it fails, the metadata will not be altered.  The migration process also takes steps to ensure that the file has been correctly transferred.  The final step of a migration is to delete the original copy of the file.  This is currently not performed atomically.

The 'mirror' subcommand form just copies the files to the destination.  It is equivalent to a 'migrate' without the database update and without the local file removal.

The 'reclaim' subcommand attempts to reclaim "<amount>" bytes of local disc space by migrating files.  Files are selected for migration by scoring them using the configured scoring algorithm and parameters.  We then choose files with the highest scores.  The "<amount>" argument should be a number (>= zero) followed by an optional scale factor; e.g. "1.1k" means 1.1 multiplied by 1024 and truncated.  Scaling factors "k", "m", "g" and "t" are supported. 

The 'ensure' subcommand is like 'reclaim', but the "<amount>" argument is interpretted as the target amount of free space to maintain on the local file system.

(As currently implemented, "reclaim" and "ensure" only support "local" as the source location.  The issue is that we don't yet have a mechanism for determining how much free space is available on locations other than "local".)

The 'score' subcommand simply scores all of the local files and lists their details in descending score order. 

The 'destinations' subcommand lists the configured transfer destinations.

The complete set of options is as follows:

  * -d, --dest=Location selects the target location for the migrate, mirror and reclaim subcommands.
  * -s, --source=Location selects the source location for the migrate, mirror and reclaim subcommands.  The default is "local".
  * --all used with migrate and mirror to select all Datafiles for the action.
  * -v, --verbosity=0,1,2,3 controls how much output the command produces.
  * --dryRun lists the files that would be migrated, mirrored or restored, but does not change anything.  (Currently, it doesn't check to see if the migrate / restore / mrror actions would have worked.)
  * --noRemove used with "migrate" to stop the removal of the file at the source location.  (This is implied in the case of mirroring.)
  * --help prints 'migratefiles' command help.

The "archive" Command
=====================

The "archive" command creates and records archival copies of the data files and metadata comprising an Experiment.

Usage
~~~~~
``./bin/django archive [<id> ...]``

.. option:: -l LOCATION, --location=LOCATION
.. option:: -d PATHNAME, --directory=PATHNAME
.. option:: --verbosity={0,1,2,3}
.. option:: -n, --dryRun
.. option:: --removeData
.. option:: --removeAll
.. option:: -i, --incremental
.. option:: -o, --sendOffline
.. option:: -c, --checksums
.. option:: -k, --keepOnly=COUNT
.. option:: --minSize=SIZE
.. option:: --maxSize=SIZE
.. option:: --maxTotalSize=SIZE
.. option:: -f, --force
.. option:: -a, --all

There are two ways to select Experiments for archiving.  You can list one or more Experiment ids and argument. Alternatively, the "--all" option selects all Experiments for archiving.  A separate archive will be created for each Experiment.  These are gzip'd tar files containing the data files together with a METS format manifest.

The "--location" and "--directory" options determine where the archives are sent.  If --directory is used, the archives are saved to a local directory.  Otherwise, they are transferred to the selected Location, defaulting to a configured Location.

When an Experiment is archived to a Location, a record is added to the Archive table to facilitate retrieval and possible restoration in the future. 

Incremental archiving works by checking to see if an Experiment (or its component Datafiles) have changed since the last archive.  If it does not appear to have, then we don't create a new archive.  Unfortunately, the MyTardis data model has a few issues that make incremental archinving less than perfect:

  * There are no timestamps on Datasets, so the addition or removal of a Datafile won't trigger an incremental archive.
  * There are no timestamps on PropertySets, so a change in the metadata won't trigger am incremental archive.
  * The timestamps on Datafiles are not populated or updated automatically.  It is left to (non-core) ingestion mechanisms to do this.  Hence, the behaviour of incremental archiving is liable to be site specific.

You can also choose to remove the online Replicas of the archived Datafiles (replacing them with offline Replicas), or to remove all Experiment / Dataset / Datafile data and metadata.  Note that a Dataset (and its Datafiles) will not be removed if it is in multiple Experiments.  To make that happen, you need to (fully) remove all of the Experiments involved.

The --keepOnly=COUNT option provides a simplistic mechanism for controlling the number of archives that are kept.  After transfering an archive, the command checks how many archives exist (in the Archive table) for the experiment being processed.  Any archives in excess of COUNT are deleted (from the Archive table and the transfer location), retaining only the COUNT most recently created archives.  It makes most sense to use --keepOnly in conjunction with --incremental.

The complete set of options is as follows:

  * -l, --location=Location specifies a Location for archiving to.
  * -d, --directory=Pathname specifies a local directory to write the archives to.
  * --all select all Experiments for the action.
  * -v, --verbosity=0,1,2,3 controls how much output the command produces.
  * --dryRun lists the files that would be migrated, mirrored or restored, but does not change anything.  (Currently, it doesn't check to see if the migrate / restore / mrror actions would have worked.)
  * --removeAll remove all online information about the Experiment and its dependent Datasets and Datafiles.
  * --removeData replace the online Replicas with a single offline one, and delete the online copies of the data.  The metadata remains online.
  * -i, --incremental enables incremental archiving 
  * -o, --sendOffline if the transfer provider and destination support this, a transferred archive is pushed offline once verified.
.. option:: -c, --checksums force the transferred archive to be verified against the checksums.  (The default is provider specific.)
.. option:: -k, --keepOnly=COUNT only keep COUNT archives for the Experiments being processed.  
.. option:: --minSize=SIZE archives smaller than this are not saved / transferred
.. option:: --maxSize=SIZE archives larger than this are not saved / transferred
.. option:: --maxTotalSize=SIZE this gives an upper limit on the total size of archives created by the run
.. option:: -f, --force turns --minSize and --maxSize into warnsings; i.e. the archives are saved anyway
  * --help prints the 'archive' command help.

The "archivelist" Command
=========================

The "archivelist" command queries and lists the records in the Archive table

Usage
~~~~~
``./bin/django archivelist [<id> ...]``

.. option:: -A, --showAll
.. option:: -F, --showFirst
.. option:: --verbosity={0,1,2,3}
.. option:: -c, --count
.. option:: -e, --experimentDate
.. option:: -u, --user=USERNAME
.. option:: -t, --title=TITLE
.. option:: -d, --date=ISO_DATE_OR_DATETIME
.. option:: -f, --fromDate=ISO_DATE_OR_DATETIME.
.. option:: -t, --toDate=ISO_DATE_OR_DATETIME.

The command either lists or counts records in the Archive table.  (It doesn't check that the archive files are still present.)

Conceptually, the procedure is as follows:
  1. An initial set of experiments is chosen; i.e. the experiments whose ids are listed as command arguments, or "all experiments" if none are listed.  (We don't check that the ids correspond to Experiments in the Experiment table.)
  1. Select all recorded archives for the selected experiments.
  1. Filter out all archives that don't match the specified --user, --title and / or date range.
  1. Depending on the presence of --showAll or --showFirst, select either the earliest, the latest or all remaining archive records for each experiment.
  1. Either show (list) or count the archive records.

The output listing shows 4 fields:
  * The experiment id
  * The experiment owner (at the time it was archived)
  * The archive_created date (or experiment_updated; see below)
  * The archive URL

Date options give dates or datetime values in ISO format; i.e. <YYYY>-<MM>-<DD> or <YYYY>-<MM>-<DD>T<HH>:<MM>:<SS>.  Values are in local time.  If the date format is used, it is interpretted as the first millisecond of the day or the last millisecond of the day, for range starts and range ends respectively.

The complete set of options is as follows:

  * -A, --showAll if present, show all selected record, not just the latest one
  * -F, --showFirst if present, show the first selected record, not the last one
  * --verbosity={0,1,2,3} controls the level of output
  * -c, --count if present, count records rather than listing them
  * -e, --experimentDate if present, use the 'experiment_updated' field rather than the 'archive_created' field for selection, ordering and display
  * -u, --user=USERNAME restrict to records with the specified owner
  * -t, --title=TITLE restrict to records with the specified title
  * -f, --fromDate=ISO_DATE_OR_DATETIME restrict to records with a date on or after the specified date or datetime.  
  * -t, --toDate=ISO_DATE_OR_DATETIME restrict to records with a date on or before the specified date or datetime.  
  * -d, --date=ISO_DATE_OR_DATETIME this is a short cut for --fromDate=ISO_DATE_OR_DATETIME, --toDat=ISO_DATE_OR_DATETIME
  * --help prints the 'archive' command help.

Architecture
============

TBD

Implementation
==============

By default, only Datafile replicas that are marked as verified can be migrated.  We depend on the file matching its checksums after copying as a check that the file has been migrated correctly.

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

We currently support two ways of checking that a file has been transferred correctly.  The preferred way is to get the transfer destination to calculate and return the metadata (checksums and length) for its copy of the file.  If that fails (or is not supported), the fallback is to read back the file from the destination and do the checksumming locally.

Normally, we require there to be either an MD5 or SHA512 checksum in the metadata.  However if 'trust_length' is set, we will accept matching file lengths as being sufficient to verify the transfer.  That would normally be a bad idea, but if the transfer process is sufficiently reliable, file length checking may be sufficient.  (In this mode, a transfer provider could get away with sending a HEAD request and using the "Content-length".)
