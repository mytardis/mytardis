#################################################
MyTardis Hierarchical Storage Management(HSM) App
#################################################


***********************
Overview
***********************
The MyTardis Hierarchical Storage Management app allows MyTardis deployments to view online/offline(disk/tape) status for a file on a
HSM file storage system.
This app also allow users to request recalling individual datafile or a dataset that has been moved to tape.


***********************
Usage
***********************

To enable the app, include :py:mod:`tardis.apps.hsm` in
:py:const:`settings.INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS += (
        'tardis.apps.hsm',
    )

This app will only try to find online/offline status for files backed by :py:class:`tardis.apps.hsm.storage.HsmFileSystemStorage`.

To configure a :py:class:`tardis.tardis_portal.models.storage.StorageBox` as a type of HSM file system, update following details for a storage box:

``Django storage class`` as ``tardis.apps.hsm.storage.HsmFileSystemStorage``

Also update following ``Storage Box Attributes``

    * Key as ``remote_path`` and value as path to remote HSM filesystem share e.g: ``vault-v2.erc.monash.edu/abc/vault``

    * Key as ``mount`` and value as mount point for above remote path e.g: ``/srv/abc_vault``


Default settings for this app is available at :py:mod:`tardis.apps.hsm.default_settings`