Changelog
=========

2.0 - Unreleased
----------------
* Auth/Auth redesign [Gerson, Uli, Russel]

  * Authorisation. Support for several pluggable authorisation plugins
    (Django internal, LDAP, VBL). The added AuthService middleware
    provides a mechanism to query all available auth modules to
    determine what group memberships a users has.

  * Alternative authorisation. Rule based experiment access control
    engine was implemented with the following access attributes for
    indivdual users and groups: canRead, canWrite, canDelete,
    isOwner. Additionally, a time stamp can be specified for each
    access rule.

    Further information can be found at the wiki: `Authorisation
    Engine design
    <http://code.google.com/p/mytardis/wiki/AuthorisationEngineAlt>`_

* New METS parser [Gerson]
* Dist/Buildout infrastructure [Russell]
* Through the web creation and editing of experiments [Steve, Russell]
* Through the web upload of files [Steve]


1.07 - 01/06/2010
-----------------

* Publish to tardis.edu.au interface created, though not implemented,
  pending legal text


1.06 - 15/03/2010
-----------------
* Parameter import interface for creation of new parameter/schema
  definitions
* iPhone Interface


1.05 - 01/03/2010
-----------------

* Images as parameters supported
* Data / metadata transfer from synchrotron is now 'threaded' using
  asynchronous web service transfers.


1.0 - 01/02/2010
----------------

* MyTARDIS created from existin MyTARDIS python / django codebase
* Allows private data to be stored
* Open key/value parameter model, replacing current crystallography
  one
* Internal data store for data
* LDAP Login
* Pagination of files
* Creation of synchrotron-tardis from MyTARDIS codebase including
  specific code for the VBL login service and data transfer to
  MyTARDIS deployments.
* Web server changed to apache and mod_wsgi


0.5 - 2009
----------

* Re-wrote federated index (python / django)
* Federated stores are now simple web server based with optional FTP
  access
* Runs on Jython / Tomcat


0.1 - 2007
----------

* Federated index (php) running on Apache HTTP Server
* Crystallography data deposition and packaging tools for Fedora
  Commons (java swing desktop)
* Search Interface via web
