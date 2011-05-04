
.. _ref-authframework:

:mod:`~tardis.tardis_portal.auth` -- Auth Framework
===================================================

.. py:module:: tardis.tardis_portal.auth
.. moduleauthor:: Ulrich Felzmann <ulrich.felzmann@versi.edu.au>
.. moduleauthor:: Gerson Galang <gerson.galang@versi.edu.au>
.. moduleauthor:: Russell Sim <russell.sim@monash.edu>

The main purpose of the reworked Auth system is to allow per
experiment permissions to exist allowing a richer web experience.
Because of this the permissions are applied on a per experiment basis
with a few predefined roles.

**read**
   read permission allows individuals and groups access to view an
   experiment.

**write**
   write permissions cover addition of new datasets and datafiles
   and also deletion of datafile.

**delete**
   delete permission allows deletion of datasets and experiments.

Roles are applied through the web using the *Control Panel* and can be
applied to either users or groups.

To make an experiment public requires and explicit publish action.

In the *settings.py* user providers are activated by specifying them
within the **USER_PROVIDERS** variable::

   USER_PROVIDERS = ('tardis.tardis_portal.auth.localdb_auth.DjangoUserProvider',)

In the *settings.py* group providers are activated by specifying them
within the **GROUP_PROVIDERS** variable::

   GROUP_PROVIDERS = ('tardis.tardis_portal.auth.localdb_auth.DjangoGroupProvider',
                      'tardis.tardis_portal.auth.vbl_auth.VblGroupProvider',)


:py:class:`AuthService` Objects
-------------------------------
.. autoclass:: AuthService
   :members:
   :undoc-members:

Auth Plugins
------------

* :py:mod:`tardis.tardis_portal.auth.localdb_auth`
* :py:mod:`tardis.tardis_portal.auth.ldap_auth`
* :py:mod:`tardis.tardis_portal.auth.ip_auth`
* :py:mod:`tardis.tardis_portal.auth.vbl_auth`
