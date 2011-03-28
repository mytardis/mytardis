:py:mod:`tardis.tardis_portal.auth.ldap_auth` -- LDAP Authentication
====================================================================

.. _ref-ldap_auth:

.. py:module:: tardis.tardis_portal.auth.ldap_auth
.. moduleauthor:: Gerson Galang <gerson.galang@versi.edu.au>
.. moduleauthor:: Russell Sim <russell.sim@gmail.com>


:py:func:`ldap_auth` Function
------------------------------
.. autofunction:: ldap_auth

.. attribute:: tardis.settings_changeme.LDAP_TLS

   Enable TLS connections.

.. attribute:: tardis.settings_changeme.LDAP_URL

   Set the URL of the LDAP server, e.g. *ldap://localhost:389*

.. attribute:: tardis.settings_changeme.LDAP_USER_LOGIN_ATTR

   Set the login attribute of the users, usually this will be either
   *cn* or *uid*

.. attribute:: tardis.settings_changeme.LDAP_USER_ATTR_MAP

    The LDAP user attribute map is used to map internal identifiers
    like *display* and *email* to their LDAP equivalents e.g.
    *{"givenName": "display", "mail": "email"}*

.. attribute:: tardis.settings_changeme.LDAP_GROUP_ID_ATTR

    This is where you specify the group identifier from LDAP, usually
    it will be *cn*.

.. attribute:: tardis.settings_changeme.LDAP_GROUP_ATTR_MAP

    This map is used to map internal identifiers like *display* e.g.
    *{"description": "display"}*

.. attribute:: tardis.settings_changeme.LDAP_BASE

   Sets the search base of the LDAP queries *dc=example, dc=com*

.. attribute:: tardis.settings_changeme.LDAP_USER_BASE

   Sets the search base of user related LDAP queries e.g. *"ou=People,
   " + LDAP_BASE*

.. attribute:: tardis.settings_changeme.LDAP_GROUP_BASE

   Sets the search base of group related LDAP queries e.g. *"ou=Group,
   " + LDAP_BASE*


:class:`LDAPBackend` Objects
----------------------------
.. autoclass:: LDAPBackend
   :members:
   :undoc-members:

