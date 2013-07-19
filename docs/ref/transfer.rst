.. _ref-transfer:

:mod:`~tardis.tardis_portal.transfer` -- The File Transfer Framework
====================================================================

.. py:module:: tardis.tardis_portal.transfer
.. moduleauthor:: Stephen Crawley <s.crawley@uq.edu.au>

The Transfer module provides a framework for synchronous transfer of
files between MyTardis Locations.  Each Location has its own 
Transfer_Provider instance, configured with the location's base url,
and various provider-specific parameters.

The *settings.py* file defines the different kinds of provider in the
**TRANSFER_PROVIDERS** variable::

TRANSFER_PROVIDERS = {
    'http': 'tardis.tardis_portal.transfer.SimpleHttpTransfer',
    'dav': 'tardis.tardis_portal.transfer.WebDAVTransfer',
    'local': 'tardis.tardis_portal.transfer.LocalTransfer',
    'scp': 'tardis.tardis_portal.transfer.ScpTransfer'}

The provider for a Location is configured in the Location object by specifying
the Location's url, a provider type (one of the keys in the map above), and a
set of provider parameters.  The latter are simple name value pairs that the 
specified provider class understands.  The initial provider settings may be 
included in the **INITIAL_LOCATIONS** variable.

The provider parameters are as follows:

  * 'trust_length' (values 'True' or 'False') determines whether the 
    transfer validator will treat the length of the transferred file as
    sufficient to prove that a file transferred correctly.  (If 'False',
    a matching checksum is required.)
  * 'min_size', 'max_size' and 'maxTotalSize' (values scaled integers) give 
    default values for file size bounds.  (These are implemented by the
    "archive" command rather than the transfer provider itself.)
  * Http / WebDAV parameters:
    * 'user' gives the user name used for remote requests
    * 'password' gives the password used for remote requests
    * 'realm' gives the realm used for remote requests
    * 'scheme' gives the authentication scheme used for remote requests; 
      i.e. "basic" or "digest".
  * Scp parameters:
    * 'username' gives the remote SSH / SCP user name
    * 'key_filename' gives the pathname of the file containing the private
      key that matches the public key in the remote user's "authorized_users"
      file.  Note that password-based authentication is not supported.
    * 'command_*' these properties configure the commands and parameters used
      to make remote requests.  We use Python template substitution, with a set
      of parameters populated from the context in which we are making the
      request.

      The commands currently recognized are:
        * 'echo' used for testing aliveness.
        * 'length' used to get a remote file's length
        * 'mkdirs' used to ensure a directory path exists
        * 'remove' used to remove a file
        * 'take_offline' used with --sendOffline
        * 'scp_to' do an SCP transfer to the location
        * 'scp_from' do an SCP transfer from the location
        * 'ssh' build the SSH command (typically) used in other commands.
        * 'pre-put-file', 'pre-put-replica', 'pre-put-archive' are hooks
          that are run before doing a 'put_file', 'put_replica' or 
          'put_archive' respectively.  The 'pre_put_file' hook is a default
          for the other two hooks.
        * 'post-put-file', 'post-put-replica', 'post-put-archive' are
          equivalent post transfer hooks.
      
      The parameters available include the following, depending on the
      context:

        * 'ssh' the SSH command (built by expanding the 'ssh' template)
        * 'ssh_opts' the standard SSH command options for the port number
          and ssh key file if required.
        * 'scp_opts' the standard SCP command options for the port number
          and ssh key file if required.
        * 'hostname' the remote hostname (from the base URL)
        * 'username' the user name for the remote
        * 'path' the path part of the url (most commands)
        * 'dirname' the dirname part of the 'path' (for hooks)
        * 'basename' the basename part of the 'path' (for hooks)
        * 'remote' the path part of the url for SCP commands
        * 'local' the local file path for SCP commands

