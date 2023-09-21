# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2011, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
LDAP Authentication module.

.. moduleauthor:: Gerson Galang <gerson.galang@versi.edu.au>
.. moduleauthor:: Russell Sim <russell.sim@monash.edu>
.. moduleauthor:: Chris Seal <c.seal@auckland.ac.nz> - Updated for ldap3
"""


import logging

from django.conf import settings

from ldap3 import SAFE_SYNC, Connection, Server
from ldap3.core.exceptions import LDAPExceptionError, LDAPInvalidCredentialsResult
from ldap3.utils.conv import escape_filter_chars
from ldap3.utils.dn import escape_rdn

from ..models import UserAuthentication
from .interfaces import AuthProvider, GroupProvider, UserProvider

logger = logging.getLogger(__name__)


auth_key = "ldap"
auth_display_name = "LDAP"


class LDAPBackend(AuthProvider, UserProvider, GroupProvider):
    def __init__(
        self,
        name,
        uri,
        port,
        base,
        login_attr,
        user_base,
        user_attr_map,
        group_id_attr,
        group_base,
        group_attr_map,
        admin_user="",
        admin_pass="",
    ):
        self.name = name

        # Basic info
        self._uri = uri
        self._port = port
        self._base = base

        # Authenticated bind
        self._admin_user = admin_user
        self._admin_pass = admin_pass

        # Login attribute
        self._login_attr = login_attr

        # User Search
        self._user_base = user_base
        self._user_attr_map = user_attr_map
        self._user_attr_map[self._login_attr] = "id"

        # Group Search
        self._group_id = group_id_attr
        self._group_base = group_base
        self._group_attr_map = group_attr_map
        self._group_attr_map[self._group_id] = "id"

    #
    # AuthProvider
    #
    def authenticate(self, request):
        username = request.POST["username"]
        password = request.POST["password"]

        if not username or not password:
            return None

        server = None

        if settings.LDAP_USE_LDAPS:
            server = Server(
                f"ldaps://{settings.LDAP_URI}", port=settings.LDAP_PORT, use_ssl=True
            )
        else:
            server = Server(f"ldap://{settings.LDAP_URI}", port=settings.LDAP_PORT)

        try:
            return self._authenticate_with_LDAP(username, server, password)
        except LDAPExceptionError as err:
            logger.error(f"LDAP error {err}", exc_info=True)
            return None
        except IndexError:
            logger.error("LDAP has no results")
            return None

    def _authenticate_with_LDAP(self, username, server, password):
        user_rdn = f"{self._login_attr}={username}"
        user_dn = f"{user_rdn},{self._user_base}"
        try:
            conn = self._bind(server, user_dn, password)
            logger.debug(conn.bound)
            conn.unbind()
        except LDAPInvalidCredentialsResult:
            logger.error(f"Invalid credentials for user {username}", exc_info=True)
            return None
        # except LDAPSessionTerminatedByServerError:
        # We failed to bind using the simple method of constructing
        # the userDN, so let's query the directory for the userDN.
        # if self._admin_user and self._admin_pass:
        #    admin_dn = f"{self._login_attr}={self._admin_user},{self._user_base}"
        #    logger.debug("Using Admin account")
        #    conn = self._bind(server, admin_dn, self._admin_pass)
        #    logger.debug(conn.bound)
        #    ldap_result = conn.search(self._base, user_rdn)
        #    userDN = ldap_result[0][0]
        #    conn.unbind()
        #    conn = self._bind(server, userDN, password)
        #    logger.debug(conn.bound)
        #    conn.unbind()

        # No LDAPError raised so far, so authentication was successful.
        # Now let's get the attributes we need for this user:
        if self._admin_user and self._admin_pass:
            # admin_dn = f"{self._login_attr}={self._admin_user},{self._user_base}"
            conn = self._bind(server, self._admin_user, self._admin_pass)
            retrieveAttributes = list(self._user_attr_map.keys()) + [self._login_attr]
            ldap_result = conn.search(
                self._base,
                f"({user_rdn})",
                attributes=retrieveAttributes,
            )
            logger.debug(ldap_result)
            conn.unbind()
            if (
                ldap_result[2][0]["raw_attributes"][self._login_attr][0]
                == username.encode()
            ):
                # check if the given username in combination with the LDAP
                # auth method is already in the UserAuthentication table
                user = ldap_result[2][0]["raw_attributes"]
                return {
                    tardis_key: user[ldap_key][0].decode()
                    for ldap_key, tardis_key in self._user_attr_map.items()
                }
        return None

    def _bind(self, server, user_dn, password):
        conn = Connection(
            server,
            user=user_dn,
            password=password,
            client_strategy=SAFE_SYNC,
            raise_exceptions=False,
        )
        logger.debug(server)
        logger.debug(user_dn)
        if settings.LDAP_USE_LDAPS:
            logger.debug("Starting TLS")
            conn.start_tls()
        logger.debug("Connection established")
        logger.debug(conn.result)
        conn.bind()
        logger.debug("Connection bound")
        logger.debug(conn.bound)
        return conn

    def _query(self, base, filterstr, attrlist):
        """Safely query LDAP"""
        server = None
        conn = None

        if settings.LDAP_USE_LDAPS:
            server = Server(settings.LDAP_URI, port=settings.LDAP_PORT, use_ssl=True)
        else:
            server = Server(settings.LDAP_URI, port=settings.LDAP_PORT)

        try:
            if self._admin_user and self._admin_pass:
                conn = self._bind(server, self._admin_user, self._admin_pass)
            else:
                return None
        except LDAPExceptionError as err:
            logger.error(err, exc_info=True)
            if conn:
                conn.unbind()
            return None

        safe_dc = escape_rdn(filterstr)
        safe_filter = escape_filter_chars(safe_dc)
        dn = f"dc={safe_filter}"

        try:
            ldap_result = conn.search(base, dn, attributes=attrlist)
            return ldap_result[2][0]["raw_attributes"]
        except LDAPExceptionError as err:
            logger.error(err, exc_info=True)
        finally:
            conn.unbind()
        return None

    def get_user(self, user_id):
        return self.getUserById(user_id)

    #
    # User Provider
    #
    def getUserById(self, id):
        """
        return the user dictionary in the format of::

            {"id": 123,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com"}

        """
        result = self._query(
            self._user_base,
            "(%s=%s)" % (self._login_attr, id),
            list(self._user_attr_map.keys()) + [self._login_attr],
        )

        user = {}

        if not result:
            return None

        for key, val in result.items():
            user[self._user_attr_map[key]] = val[0].decode()
        return user

    def getUsernameByEmail(self, email):
        if "@" not in email:
            # input is username not email so return username
            return email

        server = None
        conn = None
        try:
            if settings.LDAP_USE_LDAPS:
                server = Server(
                    settings.LDAP_URI, port=settings.LDAP_PORT, use_ssl=True
                )
            else:
                server = Server(settings.LDAP_URI, port=settings.LDAP_PORT)
            if self._admin_user and self._admin_pass:
                admin_dn = f"{self._login_attr}={self._admin_user},{self._user_base}"
                conn = self._bind(server, admin_dn, self._admin_pass)
            else:
                return None
            retrieveAttributes = [self._login_attr]
            searchFilter = "(|(mail=%s)(mailalternateaddress=%s))" % (email, email)
            ldap_result = conn.search(
                self._base, searchFilter, attributes=retrieveAttributes
            )
            ldap_result = conn.entries

            logger.debug(ldap_result)
            if ldap_result[2][0]["raw_attributes"][self._login_attr][0]:
                return ldap_result[2][0]["raw_attributes"][self._login_attr][0]
            return None

        except LDAPExceptionError:
            logger.exception("ldap error", exc_info=True)
            return None
        except IndexError:
            logger.exception("index error")
            return None
        finally:
            if conn:
                conn.unbind()

    #
    # Group Provider
    #
    def getGroups(self, user):
        """return an iteration of the available groups."""
        try:
            # check if a user exists that can authenticate using the ldap
            # auth method
            userAuth = UserAuthentication.objects.get(
                userProfile__user=user, authenticationMethod=self.name
            )
        except UserAuthentication.DoesNotExist:
            return
        result = self._query(
            self._group_base,
            "(&(objectClass=posixGroup)(%s=%s))" % ("memberUid", userAuth.username),
            list(self._group_attr_map.keys()),
        )
        if not result:
            return

        for _, attr in result:
            yield attr[self._group_id][0].decode()

    def getGroupById(self, id):
        """return the group associated with the id::

        {"id": 123,
        "display": "Group Name",}

        """
        result = self._query(
            self._group_base,
            "(&(objectClass=posixGroup)(%s=%s))" % (self._group_id, id),
            list(self._group_attr_map.keys()),
        )
        if not result:
            return None

        group = {}
        for key, val in result[0][1].items():
            group[self._group_attr_map[key]] = val[0].decode()
        return group

    def searchGroups(self, **filter):
        reverse_attr = {}
        for key, val in self._group_attr_map.items():
            reverse_attr[val] = key

        qstr = ""
        for key, val in filter.items():
            qstr += "(%s=%s)" % (reverse_attr[key], val)
        result = self._query(
            self._group_base,
            "(&(objectClass=posixGroup)%s)" % qstr,
            list(self._group_attr_map.keys()) + ["memberUid"],
        )
        if not result:
            return

        for _, attr in result:
            group = {}
            for key, val in attr.items():
                if key in self._group_attr_map:
                    group[self._group_attr_map[key]] = val[0].decode()
            group["members"] = [member.decode() for member in attr["memberUid"]]
            yield group

    def getGroupsForEntity(self, id):
        """return a list of groups associated with a particular entity id"""
        result = self._query(
            self._group_base,
            "(&(objectClass=posixGroup)(%s=%s))" % ("memberUid", id),
            list(self._group_attr_map.keys()),
        )
        if not result:
            return

        for _, attr in result:
            group = {}
            for key, val in attr.items():
                group[self._group_attr_map[key]] = val[0].decode()
            yield group


_ldap_auth = None


def ldap_auth(force_create=False):
    """Return an initialised LDAP backend."""
    global _ldap_auth
    if _ldap_auth and not force_create:
        return _ldap_auth
    try:
        base = settings.LDAP_BASE
    except:
        raise ValueError("LDAP_BASE must be specified in settings.py")

    try:
        uri = settings.LDAP_URI
    except:
        raise ValueError("LDAP_URI must be specified in settings.py")

    try:
        port = settings.LDAP_PORT
    except:
        port = 389

    try:
        admin_user = settings.LDAP_ADMIN_USER
    except:
        admin_user = ""

    try:
        admin_password = settings.LDAP_ADMIN_PASSWORD
    except:
        admin_password = ""

    try:
        user_login_attr = settings.LDAP_USER_LOGIN_ATTR
    except:
        raise ValueError("LDAP_USER_LOGIN_ATTR must be specified in settings.py")

    try:
        user_base = settings.LDAP_USER_BASE
    except:
        raise ValueError("LDAP_USER_BASE must be specified in settings.py")

    try:
        user_attr_map = settings.LDAP_USER_ATTR_MAP
    except:
        raise ValueError("LDAP_USER_ATTR_MAP must be specified in settings.py")

    try:
        group_id_attr = settings.LDAP_GROUP_ID_ATTR
    except:
        raise ValueError("LDAP_GROUP_ID_ATTR must be specified in settings.py")

    try:
        group_base = settings.LDAP_GROUP_BASE
    except:
        raise ValueError("LDAP_GROUP_BASE must be specified in settings.py")

    try:
        group_attr_map = settings.LDAP_GROUP_ATTR_MAP
    except:
        raise ValueError("LDAP_GROUP_ATTR_MAP must be specified in settings.py")

    _ldap_auth = LDAPBackend(
        "ldap",
        uri,
        port,
        base,
        user_login_attr,
        user_base,
        user_attr_map,
        group_id_attr,
        group_base,
        group_attr_map,
        admin_user,
        admin_password,
    )
    return _ldap_auth
