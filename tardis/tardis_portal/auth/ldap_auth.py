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
from django.contrib.auth.models import User

from tardis.tardis_portal.models import UserProfile, UserAuthentication


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
        l.unbind_s()
        return result[0][1]['uid'][0]

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
        Searchfilter = 'uid=' + Username

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


def get_or_create_user(email):
    username = get_ldap_username_for_email(email)
    return _get_or_create_user_with_username(username)


def _get_or_create_user_with_username(username):
    user = None
    try:
        user = UserAuthentication.objects.get(username=username,
            authenticationMethod=auth_key).userProfile.user
    except UserAuthentication.DoesNotExist:
        # else, create a new user with a random password
        name = 'ldap_%s' % username[0:25]
        user = User(username=name,
            password=User.objects.make_random_password(),
            email=username)
        user.is_staff = True
        user.save()

        userProfile = UserProfile(authcate_user=True, user=user)
        userProfile.save()

        userAuth = UserAuthentication(userProfile=userProfile,
            username=username, authenticationMethod=auth_key)
        userAuth.save()
    return user


class LdapBackend():
    def authenticate(self, request):
        username = request.POST['username']
        password = request.POST['password']
        if not username or not password:
            return None

        l = None
        l_bind = None
        try:
            l = ldap.open(settings.LDAP_URL)
            searchScope = ldap.SCOPE_SUBTREE
            # retrieve all attributes - again adjust to your needs
            # see documentation for more options
            retrieveAttributes = None
            searchFilter = 'uid=' + username

            l.protocol_version = ldap.VERSION3
            result = l.search_s(settings.BASE_DN, searchScope,
                                searchFilter, retrieveAttributes)
            DN = result[0][0]
            l_bind = ldap.open('directory.monash.edu.au')
            l_bind.simple_bind_s(DN, password)

            # check if the given username in combination with the VBL
            # auth method is already in the UserAuthentication table
            return _get_or_create_user_with_username(username)

        except ldap.LDAPError:
            return None
        except IndexError:
            return None
        finally:
            if l:
                l.unbind_s()
            if l_bind:
                l_bind.unbind_s()

    def get_user(self, user_id):
        raise NotImplemented()
