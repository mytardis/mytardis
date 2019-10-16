##############################
MyTardis Social Authentication
##############################

***********************
Overview
***********************
The MyTardis social auth app allows MyTardis deployments to accept logins using
OAuth and OpenID Connect. It builds on the
`Python social auth package <https://python-social-auth.readthedocs.io/en/latest/>`_,
and uses the `Django social auth app <https://python-social-auth.readthedocs.io/en/latest/configuration/django.html>`_.

***********************
Usage
***********************

To enable the app, include :py:mod:`social_django` and :py:mod:`tardis.apps.social_auth` in
:py:const:`settings.INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS += (
        'social_django',
        'tardis.apps.social_auth',
    )

***********************
Adding backends
***********************

You will need to add authentication backends that you want to enable.
To enable Google authentication add following :py:const:`AUTHENTICATION_BACKENDS` to *settings.py*

.. code-block:: python

    AUTHENTICATION_BACKENDS += (
        'social_core.backends.open_id.OpenIdAuth',
        'social_core.backends.google.GoogleOpenId',
        'social_core.backends.google.GoogleOAuth2',
    )

To enable Australian Access federation(AAF) OpenID connect Provider(OIDC)
authentication add following :py:const:`AUTHENTICATION_BACKENDS` to *settings.py*

.. code-block:: python

    AUTHENTICATION_BACKENDS += (
        'tardis.apps.social_auth.auth.authorisation.AAFOpenId',
    )


*******************************
Adding authentication providers
*******************************

You will need add authentication providers that you want to enable.

.. code-block:: python

    AUTH_PROVIDERS += (
                  ('Google', 'Google',
                  'social_core.backends.google.GoogleOAuth2'),
                  ('AAF','AAF',
                  'tardis.apps.social_auth.auth.authorisation.AAFOpenId'),
                  )

***************************
Adding Exception Middleware
***************************
You may want to add exception middleware provided by *python-social-auth*. To do this add following to
*settings.py*

.. code-block:: python

    MIDDLEWARE += (
        'social_django.middleware.SocialAuthExceptionMiddleware',
    )

************************
Adding Context Processor
************************
You will need to add following context processor to *settings.py*

.. code-block:: python

    TEMPLATES[0]['OPTIONS']['context_processors'].extend([
    'social_django.context_processors.backends',
    'social_django.context_processors.login_redirect'])


******************
Application setup
******************

Once the application is enabled and installed define the following settings to enable authentication behaviour.

.. code-block:: python

    SOCIAL_AUTH_AAF_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'tardis.apps.social_auth.auth.social_auth.configure_social_auth_user',
    'tardis.apps.social_auth.auth.social_auth.add_authentication_method',
    'tardis.apps.social_auth.auth.social_auth.approve_user_auth',
    'tardis.apps.social_auth.auth.social_auth.add_user_permissions',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    )

.. code-block:: python

    SOCIAL_AUTH_GOOGLE_OAUTH2_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'tardis.apps.social_auth.auth.social_auth.configure_social_auth_user',
    'tardis.apps.social_auth.auth.social_auth.add_authentication_method',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'tardis.apps.social_auth.auth.social_auth.send_admin_email',
    )

Get key and secrets from the OIDC provider that you want to enable and add following settings.


.. code-block:: python

    SOCIAL_AUTH_URL_NAMESPACE_BEGIN = 'social:begin',
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = 'Get this from Google'
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'Get this from Google'
    SOCIAL_AUTH_AAF_KEY = 'Get this from AAF'
    SOCIAL_AUTH_AAF_SECRET = 'Get this from AAF'
    SOCIAL_AUTH_AAF_AUTH_URL = 'Get this from AAF'
    SOCIAL_AUTH_AAF_TOKEN_URL = 'Get this from AAF'
    SOCIAL_AUTH_AAF_USER_INFO_URL = 'Get this from AAF'

To override MyTardis's default login page (Username / Password) with a more
appropriate page for AAF and Google authentication, you can use
https://github.com/mytardis/mytardis-aaf-google-login

