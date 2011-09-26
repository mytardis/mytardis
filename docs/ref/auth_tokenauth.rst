.. _ref-tokenauth:

:py:mod:`tardis.tardis_portal.auth.token_auth` -- Temporary Token Authentication
====================================================================


.. py:module:: tardis.tardis_portal.auth.token_auth
.. moduleauthor:: Ryan Braganza <ryan@intersect.org.au>

To use token authentication, you'll need to specify the following
*settings.py*

'tardis.tardis_portal.auth.token_auth.TokenGroupProvider',

TOKEN_EXPIRY_DAYS = 30

TOKEN_LENGTH = 30

TOKEN_USERNAME = 'tokenuser'

and create a user with

bin/django createtokenuser

Cleaning up
------------------------------------------
bin/django cleanuptokens

It is recommended that you schedule regular purging of expired tokens.
Set a cronjob to run bin/django cleanuptokens


Expiry
--------------------------------
Token auth works by hijacking the group provider system.

MyTARDIS groups are calculated and cached when a user logs in.

This means that if a session is active, and a token becomes in valid (either through deletion or expiry) that access will still be granted.
To mitigate this, when a token user logs in, an explicit expiry is set on their session - the earlier of 4am the next day, or the session expiry date (the end of the day)

This forces the user to attempt to log in again, and be denied access.
