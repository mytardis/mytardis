################
OAI-PMH Producer
################

***********************
Using to provide RIF-CS
***********************

Minimal providers for Dublin Core and RIF-CS are included in the app.

To enable the app, include :py:mod:`tardis.apps.oaipmh` in
:py:const:`settings.INSTALLED_APPS`.

Your OAI-PMH query endpoint will be (on your dev server):
http://localhost:8000/apps/oaipmh/

*******************************
Implementing your own providers
*******************************

To allow multiple metadata formats (and types within them) the
:py:class:`tardis.apps.oaipmh.server.ProxyingServer` handles all requests and
proxies them to the providers specified in
:py:const:`settings.OAIPMH_PROVIDERS`.

You should extend :py:class:`tardis.apps.oaipmh.provider.base.BaseProvider`
or one of the existing providers if you wish to extend the functionality in a
site-specific way.

.. autoclass:: tardis.apps.oaipmh.provider.base.BaseProvider
    :members:

.. autoclass:: tardis.apps.oaipmh.server.ProxyingServer
    :members:


