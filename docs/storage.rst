==============================================
 Storage Options and Architecture in MyTardis
==============================================

Database layout
===============

Experiments contain Datasets, which in turn contain DataFiles.

Datasets
--------

Each Dataset stores all the files it contains in the same way. A "way to store
data" is called StorageBox. Hence there is a many-to-many relationship between
Datasets and StorageBoxes.

StorageBoxes
------------

StorageBoxes contain all the information needed to store a file except an id
unique to the file and storagebox.

They point to a class that implements the Django storage API.

Optional instatiation parameters for each ``StorageBox`` can be stored in
StorageBoxOptions. These are used as parameters to the storage class set in
the ``django_storage_class`` attribute of a ``StorageBox``

These parameters are string types by default. However, by
setting the optional parameter ``value_type`` to ``'pickle'``, any picklable
object can be stored here and hence used for instantiation of the storage
class.

Optional classification and other metadata can be stored in
StorageBoxAttributes.

A special case is where someone registers a file and wants to put it into
location themselves but needs to be given the place to put it (via the API).
Such situation can only be resolved with StorageBoxes that implement the
"build_save_location" function. Such StorageBoxes need to have a
StorageBoxAttribute with key "staging" and value "True".

DataFiles
---------

DataFiles are the logical representation of the file. They contain information
about the name, size, checksum, dates etc.

DataFileObjects
---------------

DataFileObjects point to the DataFile they belong to and the StorageBox they
reside in. They also have an identifier that the StorageBox uses to find the
actual file. DataFileObjects also have a date, and a state-flag.


Available backends
==================

File on disk

SWIFT Object Storage


How to store a file
===================

Ingestion via the RESTful API
-----------------------------


Appendix A: Conversion of 'Replicas'
====================================

Replicas used to be the method of file storage abstraction in MyTardis
versions 3.x. The StorageBoxes replace this. For pain-free upgrading, a
conversion has been included with the database migrations that works as
follows:

All 'Locations' that are local are converted to default (folder on disk)
StorageBoxes. All 'Locations' that are not local are converted to dummy 'link
only' StorageBoxes with the corresponding name. These can be upgraded manually
to a StorageBox with an appropriate backend after the migration has taken
place.

Max size is set to size of disk, hence for multiple locations on the same disk
this number provides no protection. This also should be set to reasonable
values manually after the migration.

Each 'Replica' of a file will be converted to a DataFileObject pointing to the
relevant StorageBox.

All files are manually reverified, so that unverified entries can be checked
for errors.
