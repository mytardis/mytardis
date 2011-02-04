Changelog
=========

1.0 - Unreleased
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
