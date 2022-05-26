.. _schemaparamsets:

=========================
Schema and Parameter Sets
=========================

MyTardis stores metadata as *Parameters*, which are grouped in to *Parameter
Sets*, which are defined by a *Schema*.

---------------
Managing Schema
---------------

Schema are managed through the Django administrative interface.
The administrative interface is normally accesible from a link similar to::

   http://domain.com:8000/admin/

Selecting "Schemas" in the adminstrative interface will display a list of the
installed schemas. Clicking on a schema displays the editor for that schema.

Schema definitions are the combination of two tables, *Schema* and
*ParameterName*.

The *Schema* fields are:

Namespace
   The namespace uniquely identifies the schema.  When exporting an
   experiment as a METS file the namespace is used as an XML Namespace, and
   thus must follow the XML standard, i.e. in the form of a URL.

   The MyTardis naming convention is::

      http://domain.com/localidentifiers/schemaname/version

Name
   The display name of the schema.

Type
   Experiment, Dataset or Datafile.

Subtype
   Used to group and identify schema for forms based searching.

The *ParameterName* fields are:

Schema
   The namespace of the schema which this parameter belongs to.

Name
   The identifier used to ingest parameters.

Full Name
   The display name of the parameter.

Units
   The display name of the units for numerical values.

Data Type
   One of:

   * Numeric
   * String
   * Longstring
   * URL
   * Filename
   * Datetime
   * Link

   Strings use the input field widget for editing, while longstrings use a
   textarea widget.

Immutable
   If true, no user editing of the parameter is allowed, regardless of access.

Comparison Type
   The type of search to be performed with Forms Based Search.
   Not used by Advanced Search.

Sensitive
   Flag whether this parameter is considered Sensitive. Sensitive metadata can only
   be interacted with (viewed/changed/deleted) if a user has sensitive_permission access
   on the Experiment(/dataset/datafile).

Is Searchable
   Flag whether this parameter is searchable.

Choices
   If defined, a drop down list of values is displayed.

Order
   The display order of the parameters within the schema.  Sorting is by
   Order, then alphabetically.
