
.. _dev-authentication:

Authentication Methods
======================


Users
-----

MyTardis supports several sources of authentication and identity, referred to
as user providers.

In the *settings.py* user providers are activated by specifying them
within the **USER_PROVIDERS** variable::

   USER_PROVIDERS = ('tardis.tardis_portal.auth.localdb_auth.DjangoUserProvider',)

Groups
------

MyTardis also supports several sources for group membership information,
referred to as group providers.

In the *settings.py* group providers are activated by specifying them
within the **GROUP_PROVIDERS** variable::

   GROUP_PROVIDERS = ('tardis.tardis_portal.auth.localdb_auth.DjangoGroupProvider',
                      'tardis.tardis_portal.auth.vbl_auth.VblGroupProvider',)


Included Auth Plugins
---------------------

.. toctree::
   :maxdepth: 1

   auth_httpbasicendpoint
   auth_ldap
   auth_tokenauth

* :py:mod:`tardis.tardis_portal.auth.ip_auth`

The :doc:`../pydoc/tardis.tardis_portal.auth` module contains the authentication
specific code.

