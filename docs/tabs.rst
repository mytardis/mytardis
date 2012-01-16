===============
Additional Tabs
===============

MyTARDIS supports pluggable tabs to provide additional information and processing on experiments.  Documentation on the configuration of additional tabs is available at :doc:`install`.

A brief introduction is provided below for each of the additional tabs supplied with MyTARDIS.

ANDS Register
-------------

The ANDS Register tab allows experiment owners to mark their experiment as available for harvesting by Research Data Australia (RDA), and optionally making the data public.

The fields include:

Authors
  An optional comma separated list of authors.  If absent, the experiment authors will be used.

Description
  An optional description of the experiment.  If absent, the experiment abstract will be used.

License
  The license under which the experiment is made available

Access Type
  The type of access to the data:

  * Unpublished - the experiment is private, i.e. only accessible to authorised MyTARDIS users
  * Private - the experiment is listed in RDA, but no access to the data or metadata is provided
  * Mediated - the experiment is listed in RDA, the experiment owner must be contacted in order to gain access to the data and metadata
  * Public - the experiment is made public, i.e. anonymous access to the data and metadata is provided, and listed in RDA with a link back to the experiment in MyTARDIS.

Related Info
------------

The Related Info tab allows experiment owners to add related publication or links to other web sites to the experiment.

Type
  ``website`` or ``publication``

Identifier Type
  See http://ands.org.au/guides/cpguide/cpgrelatedinfo.html for a list of valid identifier types, typically ``uri`` for websites or ``isbn`` for publications

Identifier
  The actual link or identifier

Title
  Optional text used to display the identifier

Notes
  Optional additional information about the identifier


Summary Table
-------------

The summary table provides an tabular view of the datafiles.  Columns may be hidden, sorted (current view only), filtered and the experiment saved as a CSV file.

