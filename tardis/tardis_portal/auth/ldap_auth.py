#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.template import Context, loader
from django.http import HttpResponse

from django.conf import settings

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, Group
from django.http import HttpResponseRedirect, HttpResponseForbidden, \
    HttpResponseNotFound, HttpResponseServerError
from django.contrib.auth.decorators import login_required

from tardis.tardis_portal.forms import RegisterExperimentForm
from tardis.tardis_portal.logger import logger

from django.core.paginator import Paginator, InvalidPage, EmptyPage

from tardis.tardis_portal.models import *

import urllib
import urllib2

import ldap

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
        return result[0][1]['uid'][0]

    except ldap.LDAPError, e:
        return ''

    except IndexError, i:
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
        searchFilter = 'uid=' + username

        l.protocol_version = ldap.VERSION3

        result = l.search_s(settings.BASE_DN, searchScope,
                            searchFilter, retrieveAttributes)

        return result[0][1]['mail'][0]
    except ldap.LDAPError, e:

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

        except ldap.LDAPError, e:
            return None
        except IndexError, i:
            return None
        finally:
            if l:
                l.unbind_s()
            if l_bind:
                l_bind.unbind_s()

    def get_user(self, user_id):
        raise NotImplemented()
