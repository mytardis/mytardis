.. _ref-httpbasicendpoint_auth:

:py:mod:`tardis.tardis_portal.auth.httpbasicendpoint_auth` -- HTTP Basic Endpoint Authentication
================================================================================================


.. py:module:: tardis.tardis_portal.auth.httpbasicendpoint_auth
.. moduleauthor:: Tim Dettrick <t.dettrick@uq.edu.au>

HTTP Basic Endpoint authentication uses access to a HTTP resource (or endpoint)
to determine if authentication should be allowed.

To use HTTP Basic Endpoint authentication, you'll need a HTTP resource
protected by HTTP Basic Auth which is accessible from the MyTardis
server.

In the *settings.py* add the following to *AUTH_PROVIDERS* with an appropriate
name. eg.

.. code-block:: python

    AUTH_PROVIDERS = (
        ('acls', 'acls', 'tardis.tardis_portal.auth.httpbasicendpoint_auth.HttpBasicEndpointAuth'),
    )

On each request, MyTardis will attempt to use basic authentication with the
provided credentials to access the HTTP resource. If it fails, access is denied.

.. attribute:: tardis.default_settings.LDAP_TLS

    Endpoint to use in HTTP Basic Endpoint Auth. eg.

    .. code-block:: python

        HTTP_BASIC_AUTH_ENDPOINT = 'https://test.example/endpoint'
