.. _schemaparamsets:

=========================
Schema and Parameter Sets
=========================

MyTARDIS stores metadata as *Parameters*, which are grouped in to *Parameter Sets*, 
which are defined by a *Schema*.

---------------
Managing Schema
---------------

MyTARDIS currently relies on the in-built Django administrative interface for managing schema.  The administrative interface is accesible from a link similar to::

   http://localhost/admin/

Schema definitions are the combination of two tables, Schema and ParameterName.

The Schema record identifies the schema (*namespace*), with a ParameterName record for 
each attribute of the schema.  Other attributes of the parameter include the type, 
e.g. string, number, URL, date, enumerated list, etc., 
whether the parameter is searchable or not,
and if it is an enumerated list, the valid choices.

Note: Creating a proper schema administration page is scheduled to be completed by December 2011.

