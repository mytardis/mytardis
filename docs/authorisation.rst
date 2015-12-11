===============
 Authorisation
===============

The old documentation is still relatively valid. This document will eventually
replace it, but until then, please refer to the different documentation in
parallel. Final authority, as always, can be found in the code.

Django Authorisation
====================

Django provides an authorisation/permission mechanism that is in use by
default.  It is enabled in MyTardis in ``default_settings.py`` together with
the custom object level permission framework described below.

.. code-block:: python

    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'tardis.tardis_portal.auth.cas.backends.CASBackend',
    	'tardis.tardis_portal.auth.authorisation.ACLAwareBackend',
    )

Using the Central Authentication Service (CAS) Backend
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To use a CAS Server for authentication the following settings must be overridden:

.. code-block:: python
	CAS_ENABLED = True
	CAS_SERVER_URL = 'https//<url of the CAS Service>/'
	CAS_SERVICE_URL = 'http://<url of the tardis instance>/'


* ``CAS_ENABLED`` must be set to ``True`` to turn on the CAS backend. This will 
  also enable the login button to redirect to the CAS server. 

* ``CAS_SERVER_URL`` must be set to the base URL of the CAS service. This can be 
  checked by using a browser to go to the login page via the URL: 
  `https//<url of the CAS Service>/login`

* ``CAS_SERVICE_URL`` must be set to the URL of the MyTardis instance. This will
  be passed to the CAS service so that it can redirect back to MyTardis after 
  authentication.

The following settings may be overridden as required:

.. code-block:: python
	CAS_LOGOUT_COMPLETELY = True
	CAS_LOGIN_URL = '/cas/login/'

* ``CAS_LOGOUT_COMPLETELY`` may be set to ``False`` if your enterprise has a 
  single sign-in policy. The user will remain logged in via CAS even if they 
  have logged out of MyTardis.

* ``CAS_LOGIN_URL`` may be overridden if an alternate login view has been 
  developed.

For more information on CAS project see: http://jasig.github.io/cas    

Permissions
^^^^^^^^^^^

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

More fine grained permission control is available in MyTardis via ACLs and a
custom permissions class.

Custom permissions are queried on the user object as well, however, with the
addition of the object in question:

.. code-block:: python

   user.has_perm('tardis_acls.change_experiment', experiment)

Verbs currently available are ``change``, ``view``, ``delete``, ``owns``,
``share``.

These permissions are set using the ``ObjectACL`` model, which is queried via
``has_perm``. ``ObjectACL`` works the same way as ``ExperimentACL`` used
to. For now, please refer to the documentation for ``ExperimentACL``s.

The translation of ACLs to ``has_perm`` verbs is defined in a function in
``tardis.tardis_portal.auth.authorisation``.

In addition to ACLs ``has_perm`` calls model functions named
``_has_VERB_perm``, which allows model-specific permission logic.

The current policy is that if those functions return True or False then that
result is returned without further checking. If they return an object,
permissions will be checked for this object thereby allowing delegation.
