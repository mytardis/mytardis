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
"""


import logging
import ldap
from ldap3.utils.dn import escape_rdn
from ldap3.utils.conv import escape_filter_chars

from django.conf import settings

from ..models import UserAuthentication
from .interfaces import AuthProvider, GroupProvider, UserProvider


logger = logging.getLogger(__name__)


auth_key = "ldap"
auth_display_name = "LDAP"


class LDAPBackend(AuthProvider, UserProvider, GroupProvider):
    def __init__(
        self,
        name,
        url,
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
        self._url = url
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

    def _query(self, base, filterstr, attrlist):
        """Safely query LDAP"""
        l = None
        searchScope = ldap.SCOPE_SUBTREE

        try:
            l = ldap.initialize(self._url)
        except ldap.LDAPError as e:
            logger.error("%s: %s" % (str(e), self._url))
            return None
        l.protocol_version = ldap.VERSION3

        try:
            if self._admin_user and self._admin_pass:
                l.simple_bind_s(self._admin_user, self._admin_pass)
            else:
                l.simple_bind_s()
        except ldap.LDAPError as e:
            logger.error(e.args[0]["desc"])
            if l:
                l.unbind_s()
            return None

        safe_dc = escape_rdn(filterstr)
        safe_filter = escape_filter_chars(safe_dc)

        dn = "dc={}".format(safe_filter)

        try:
            ldap_result_id = l.search(base, searchScope, dn, attrlist)
            _, result_data = l.result(ldap_result_id, 1)
            return result_data
        except ldap.LDAPError as e:
            logger.error(str(e))
        finally:
            l and l.unbind_s()
        return None

    #
    # AuthProvider
    #
    def authenticate(self, request):
        username = request.POST["username"]
        password = request.POST["password"]

        if not username or not password:
            return None

        l = None

        try:
            userRDN = self._login_attr + "=" + username
            l = ldap.initialize(self._url)
            l.protocol_version = ldap.VERSION3

            # To authenticate, we need the user's distinguished name (DN).
            try:
                # If all of your users share the same organizational unit,
                # e.g. "ou=People,dc=example,dc=com", then the DN can be
                # constructed by concatening the user's relative DN
                # e.g. "uid=jsmith" with self._user_base, separated by
                # a comma.
                userDN = userRDN + "," + self._user_base
                l.simple_bind_s(userDN, password)
            except ldap.INVALID_CREDENTIALS:
                logger.error("Invalid credentials for user %s" % username)
                return None
            except ldap.LDAPError:
                # We failed to bind using the simple method of constructing
                # the userDN, so let's query the directory for the userDN.
                if self._admin_user and self._admin_pass:
                    l.simple_bind_s(self._admin_user, self._admin_pass)
                ldap_result = l.search_s(self._base, ldap.SCOPE_SUBTREE, userRDN)
                userDN = ldap_result[0][0]
                l.simple_bind_s(userDN, password)

            # No LDAPError raised so far, so authentication was successful.
            # Now let's get the attributes we need for this user:
            if self._admin_user and self._admin_pass:
                l.simple_bind_s(self._admin_user, self._admin_pass)
            retrieveAttributes = list(self._user_attr_map.keys()) + [self._login_attr]
            ldap_result = l.search_s(
                self._base, ldap.SCOPE_SUBTREE, userRDN, retrieveAttributes
            )

            if ldap_result[0][1][self._login_attr][0] == username.encode():
                # check if the given username in combination with the LDAP
                # auth method is already in the UserAuthentication table
                user = ldap_result[0][1]
                return {
                    tardis_key: user[ldap_key][0].decode()
                    for ldap_key, tardis_key in self._user_attr_map.items()
                }
            return None

        except ldap.LDAPError as err:
            logger.error("LDAP error %s" % err)
            return None
        except IndexError:
            logger.error("LDAP has no results")
            return None
        finally:
            if l:
                l.unbind_s()

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

        for key, val in result[0][1].items():
            user[self._user_attr_map[key]] = val[0].decode()
        return user

    def getUsernameByEmail(self, email):
        if "@" not in email:
            # input is username not email so return username
            return email

        l = None
        try:
            retrieveAttributes = [self._login_attr]
            l = ldap.initialize(self._url)
            l.protocol_version = ldap.VERSION3
            searchFilter = "(|(mail=%s)(mailalternateaddress=%s))" % (email, email)
            ldap_result = l.search_s(
                self._base, ldap.SCOPE_SUBTREE, searchFilter, retrieveAttributes
            )

            logger.debug(ldap_result)
            if ldap_result[0][1][self._login_attr][0]:
                return ldap_result[0][1][self._login_attr][0]
            return None

        except ldap.LDAPError:
            logger.exception("ldap error")
            return None
        except IndexError:
            logger.exception("index error")
            return None
        finally:
            if l:
                l.unbind_s()

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
        url = settings.LDAP_URL
    except:
        raise ValueError("LDAP_URL must be specified in settings.py")

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
        url,
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
