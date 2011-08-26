======
Search
======

MyTARDIS supports two search mechanisms, Forms Based Search and Advanced Search.

Advanced Search
---------------

MyTARDIS uses the Apache Solr search engine to power the advanced search
functionality.  Currently the native Apache Lucene query syntax is used.

Advanced Search supports:

* Simple keyword search
* Boolean Operators and Grouping
* Field search
* Range searches

For a full description of the query syntax, please see http://lucene.apache.org/java/2_9_1/queryparsersyntax.html.


Keyword Search
~~~~~~~~~~~~~~

A simple keyword search consists of one or more terms to be searched, e.g.::

  temperature current

The example shown above will return all experiments that contain the words ``temperature`` AND ``current``.

Note that Solr uses tokenisation and supports *stemming*, so ``magnetism`` will match ``magnetic``, ``magnet``, etc.


Boolean Operators and Grouping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Boolean operators allow terms to be combined through logic operators.  Supported operators are AND, "+", OR, NOT and "-".  The operators must be in CAPITALS.

Extending the example above, to search instead for experiments that contain either of the terms ``temperature`` or ``current``::

  temperature OR current

To search for experiments that must contain ``temperature`` and may contain ``current``::

  +temperature current

To search for experiments that must not contain ``current``::

  temperature -current

Parantheses may be used to group clauses to form sub-queries.  E.g.::

  (temperature OR heat) AND current

Field Search
~~~~~~~~~~~~

All core metadata fields and soft metadata fields that have been flagged as searchable may be individually searched.  Field based syntax is to include the field name followed by a colon and the term being searched, e.g.::

  experiment_description:temperature

In this example experiments containing the word ``temperature`` in the description will be returned.

Field terms may be included in boolean and grouped expressions in the same manner as simple terms.


Range Searches
~~~~~~~~~~~~~~

Range queries allow experiments to be searched where field values are between the lower and upper bound specified by the range term, e.g.::

  datafile_temperature:[10.0 TO 20.0]

Note that the "TO" must be upper-case.

Square brackets indicate that the search should be inclusive, exclusive range queries are denoted by curly brackets, e.g.::

  datafile_temperature:{10.0 TO 20.0}

