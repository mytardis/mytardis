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
import ldap

from django.conf import settings

from tardis.tardis_portal.auth.utils import get_or_create_user_with_username
from tardis.tardis_portal.logger import logger


auth_key = u'ldap'
auth_display_name = u'LDAP'


def get_ldap_username_for_email(email):
    # return username if found, otherwise return none
    l = None
    try:
        l = ldap.open(settings.LDAP_URL)
        searchScope = ldap.SCOPE_SUBTREE

        # retrieve all attributes - again adjust to your needs
        # see documentation for more options
        retrieveAttributes = ['uid']
        searchFilter = '(|(mail=' + email + ')(mailalternateaddress=' \
            + email + '))'

        l.protocol_version = ldap.VERSION3
        result = l.search_s(settings.BASE_DN, searchScope,
                            searchFilter, retrieveAttributes)
        return result[0][1][settings.LDAP_USER_RDN][0]

    except ldap.LDAPError:
        return ''

    except IndexError:
        return ''

    finally:
        if l:
            l.unbind_s()


def get_ldap_email_for_user(username):
    # return email if found else return none

    l = None
    try:
        l = ldap.open(settings.LDAP_URL)

        searchScope = ldap.SCOPE_SUBTREE

        # retrieve all attributes - again adjust to your needs
        # see documentation for more options
        retrieveAttributes = ['mail']
        searchFilter = settings.LDAP_USER_RDN + '=' + username

        l.protocol_version = ldap.VERSION3

        result = l.search_s(settings.BASE_DN, searchScope,
                            searchFilter, retrieveAttributes)
        l.unbind_s()
        return result[0][1]['mail'][0]
    except ldap.LDAPError:
        return ''
    except IndexError, i:
        return ''
    finally:
        if l:
            l.unbind_s()


class LdapBackend():

    def authenticate(self, request):
        username = request.POST['username']
        password = request.POST['password']
        if not username or not password:
            return None

        l = None

        try:
            searchScope = ldap.SCOPE_SUBTREE
            retrieveAttributes = None
            userRDN = settings.LDAP_USER_RDN + '=' + username

            l = ldap.initialize(settings.LDAP_URL)
            l.protocol_version = ldap.VERSION3
            l.simple_bind(userRDN+','+settings.BASE_DN, password)
            ldap_result_id = l.search(settings.BASE_DN, searchScope, 
                                      userRDN, retrieveAttributes)

            result_type, result_data = l.result(ldap_result_id, 0)

            if result_data[0][1][settings.LDAP_USER_RDN][0]==username:
                # check if the given username in combination with the LDAP
                # auth method is already in the UserAuthentication table
                return get_or_create_user_with_username(request, username, auth_key)
            return None           

        except ldap.LDAPError:
            logger.error("ldap error")
            return None
        except IndexError:
            logger.error("index error")
            return None
        finally:
            if l:
                l.unbind_s()

    def get_user(self, user_id):
        raise NotImplemented()
