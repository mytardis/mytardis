=======================
Authorisation Framework
=======================


Django Authorisation
====================

Django has a built-in authorisation/permission mechanism that is in use by
default.  It is enabled in MyTardis in ``default_settings.py`` together with
the custom object level permission framework described below.

.. code-block:: python

    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'tardis.tardis_portal.auth.authorisation.ACLAwareBackend',
    )

The Django default permissions are automatically available for each Model.
The verbs are ``add``, ``change``, ``delete``, and they can be queried on the
user object as follows:

.. code-block:: python

   user.has_perm('tardis_portal.add_experiment')
   user.has_perm('tardis_portal.add_dataset')
   user.has_perm('tardis_portal.change_experiment')
   user.has_perm('tardis_portal.delete_datasetparameterset')

There is a function in ``tardis.tardis_portal.auth.authservice`` called
``_set_user_from_dict`` that adds the following permissions for each new user
created using custom methods:

.. code-block:: python

   'add_experiment'
   'change_experiment'
   'change_group'
   'change_userauthentication'
   'change_experimentacl'

These permissions apply in general and are augmented by ACLs

Object Level Permissions and Access Control Lists
=================================================


The main purpose of the ACL system is to manage per
experiment permissions. The architecture allows for future expansion to more
find grained permission management. However, at this stage only the Experiment
level is supported by the user interface.

Permissions are applied with a few predefined roles:

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

To make an experiment public requires an explicit publish action.


The ACL permissions can be queried on the user object just like standard
permissions, however, with the
addition of the object in question:

.. code-block:: python

   user.has_perm('tardis_acls.change_experiment', experiment)

Verbs currently available are ``change``, ``view``, ``delete``, ``owns``,
``share``.

The translation of ACLs to ``has_perm`` verbs is defined in a function in
``tardis.tardis_portal.auth.authorisation``.

To allow for querying on any object related to experiments, extra logic
was added to some of the models.
To support the logic, in addition to ACLs, ``has_perm`` calls model functions
named ``_has_VERB_perm``, which allows model-specific permission logic.

The current policy is that if those functions return True or False then that
result is returned without further checking. If they return an object,
permissions will be checked for this object thereby allowing delegation.
