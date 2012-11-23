=============
Migration App
=============

The migration app supports the orderly migration of data files between different storage locations under the control of a single MyTardis instance.

The initial version of the app simply provides a django admin command for manually migrating the data associated with a Datafile, Dataset or Experiment.  

TO DO:

 * Provide a framework that allows migrations to be run on a schedule, and the selection of files for migration is based on tailorable criteria, and is aware of storage availability.

 * Once the datafile has migrated, the default behaviour of MyTardis when the user attempts to fetch / view the Datafile is to fetch back a temporary copy.  Arrange that the temporary copy can be cached and/or reinstated locally.  Arrange that the files can be retrieved directly from the secondary store to the user's web browser.  (The last would involve some kind of SSO involving MyTardis and the secondary store's web server.)

 * Provide some indication to end users that datafiles have been migrated and that access will be slower.

 * Provide some mechanism for end users to influence which files are migrated, or not.

 * Work needs to be done on configuration of the destinations and providers ... so configuration details are liable to change.

Setup
=====

Add the migration application to the INSTALLED_APPS list in your MyTardis project's settings file

.. code-block:: python

    INSTALLED_APPS += (
        TARDIS_APP_ROOT + '.migration',
    )

Describe the available destinations for transferring files to.  Each destination is a dictionary in the list, and the 'name' attribute gives its name::

    MIGRATION_DESTINATIONS = [{'name': 'test', 
                               'transfer_type': 'dav',
                               'datafile_protocol': '',
                               'trust_length': False,
			       'user' : 'username',
			       'password' : 'secret',
			       'realm' : 'realmName',
			       'auth' : 'digest',
                               'base_url': 'http://127.0.0.1:4272/data/'}]

The attributes are as follows:

  * The 'name' is the name of the transfer destination, as used in the "--dest" option.
  * The 'transfer_type' is the provider type, and should match one of the keys of the MIGRATION_PROVIDERS map.
  * The 'datafile_protocol' is the value to be used in the Datafile's 'protocol' field after migration to this destination.
  * The 'trust_length' field says whether simply checking a transferred file's length (e.g. using HEAD) is sufficient verification that it transferred.
  * The 'base_url' field is used by the provider to form the target URL for the transfer.  The resulting URL will be saved in the Datafile's 'url' file folloing a successful transfer.
  * The 'user', 'password', 'realm' and 'auth' attributes provide optional credentials for the provider to use when talking to the target server.  If 'realm' is omitted (or None) then you are saying to provide the user / password irrespective of the challenge realm.  The 'auth' property can be 'basic' or 'digest', and defaults to 'digest'.

Specify the default migration destination.  If none is specified, the "--dest" option becomes mandatory for the "migrate" command::

    DEFAULT_MIGRATION_DESTINATION = 'test'

List the migration transfer provider classes.  Currently we only implement one provider, but adding custom providers should not be difficult::

    MIGRATION_PROVIDERS = {
         'http': 'tardis.apps.migration.SimpleHttpTransfer',
         'dav': 'tardis.apps.migration.WebDAVTransfer'}

The SimpleHttpTransfer provider requires a remote server that can accept GET, PUT, DELETE and HEAD requests.  Optionally, it can send a GET with a query for the remote file metadata (file size and hashes) which it will use to verify that the the file has migrated correctly before deleting the local copy.

The WebDAVTransfer provider works with a vanilla WebDAV implementation, and used MKCOL to create the "collections" to mirror the filepath structure of the files being migrarted.  (I'm using Apache Httpd's standard WebDAV modules.)  Verification is done by fetching the file back and comparing checksums. 

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


Commands
========

The initial version of the migration app provides the "migratefiles" command to perform migrations

Usage
~~~~~
``./bin/django migratefiles migrate <target> <id> ...``
``./bin/django migratefiles restore <target> <id> ...``
``./bin/django migratefiles reclaim <amount>``
``./bin/django migratefiles score``
``./bin/django migratefiles destinations``

.. option:: -d DESTINATION, --dest=DESTINATION
.. option:: --verbosity={0,1,2,3}
.. option:: -n, --dryRun
.. option:: --noRemove
.. option:: --mirror

The first form migrates the files associated with one or more DataFiles, DataSets or Experiments.  The "<target>" is one of "dataset", "datasets", "datafile", "datafiles", "experiment" or "experiments", and "<id> ..." is a sequence of object ids for objects of the target type. 

The migration of a single file is atomic.  If the migration succeeds, the Datafile metadata in MyTardis will have been updated to the new location.  If it fails, the metadata will not be altered.  The migration process also takes steps to ensure that the file has been correctly transferred.  The final step of a migration is to delete the original copy of the file.  This is currently not performed atomically.

The second form attempts to restore (bring back to local disc) the data associated with the selected DataFiles, DataSets or Experiments.  (The current implementation temporarily marks each Datafile as "not verified" and attempts to "stage" it.)

The third form attempts to reclaim "<amount>" bytes of local disc space by migrating files.  Files are selected for migration by scoring them using the configured scoring algorithm and parameters.  We then choose files with the highest scores.

The fourth form simply scores all of the local files and lists their details in descending score order. 

The final form of the command lists the configured transfer destinations.

The options are as follows:

  * --dest selects the remote location for the migrate and reclaim subcommands.  (For the restore subcommand, the destination is local, and the remote source location is implied by the Datafile's 'url' attribute.) 
  * --verbosity determines how much output is produced in the normal django command fashion.
  * --dryRun lists the files that would be migrated or restored, but does not change anything.  (Currently, it doesn't check to see if the migrate / restore would have worked.)
  * --noRemove performs the migrate or restore action, but does not remove the source file.
  * --mirror performs the file transfer, but doesn't update the database or remove the source file.

Architecture
============

TBD

Implementation
==============

Currently, only Datafiles that are local and verified can be migrated.  The reason for the latter is that we depend on the file matching its checksums when we check that the file has been migrated correctly.

When a file is migrated, the Datafile is changed as follows:

 * The 'url' field is set to the url of the file at the destination.
 * The 'protocol' field is set to the 'datafile_protocol' attribute in the destination descriptor.  The default is an empty string, which will cause MyTardis to use its built-in file fetching support to pull files back. 

We currently support two ways of checking that a file has been transferred correctly.  The preferred way is to get the transfer destination to calculate and return the metadata (checksums and length) for its copy of the file.  If that fails (or is not supported), the fallback is to read back the file from the destination and do the checksumming locally.

Normally, we require there to be either an MD5 or SHA512 checksum in the metadata.  However if 'trust_length' is set, we will accept matching file lengths as being sufficient to verify the transfer.  That would normally be a bad idea, but if the transfer process is sufficiently reliable, file length checking may be sufficient.  (In this mode, a transfer provider could get away with sending a HEAD request and using the "Content-length".)
