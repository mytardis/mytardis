#!/usr/bin/python
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

from tardis.tardis_portal.ProcessExperiment import ProcessExperiment
from tardis.tardis_portal.RegisterExperimentForm import RegisterExperimentForm

from django.core.paginator import Paginator, InvalidPage, EmptyPage

from tardis.tardis_portal.models import *

import urllib
import urllib2

import ldap


def authenticate_user_ldap(username, password):

    # return true if username and password correct

    l = None
    l_bind = None
    try:
        l = ldap.open(settings.LDAP_URL)

        searchScope = ldap.SCOPE_SUBTREE

        # # retrieve all attributes - again adjust to your needs - see documentation for more options

        retrieveAttributes = None
        searchFilter = 'uid=' + username

        l.protocol_version = ldap.VERSION3

        result = l.search_s(settings.BASE_DN, searchScope,
                            searchFilter, retrieveAttributes)

        DN = result[0][0]

        l_bind = ldap.open('directory.monash.edu.au')

        l_bind.simple_bind_s(DN, password)

        return True
    except ldap.LDAPError, e:

        return False
    except IndexError, i:

        return ''
    finally:

        if l:
            l.unbind_s()
        if l_bind:
            l_bind.unbind_s()


def get_ldap_username_for_email(email):

    # return username if found, otherwise return none

    l = None
    try:
        l = ldap.open(settings.LDAP_URL)

        searchScope = ldap.SCOPE_SUBTREE

        # # retrieve all attributes - again adjust to your needs - see documentation for more options

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

        # # retrieve all attributes - again adjust to your needs - see documentation for more options

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


# todo complete


def get_or_create_user_ldap(email):

    # ignore the 'authcate' model fieldname.. adapted from monash auth

    authcate_user = None
    username = get_ldap_username_for_email(email)
    try:

        u = User.objects.get(username=username)
        print u.get_profile()

        # if, somehow someone else has created a user manually that has this username

        if not u.get_profile().authcate_user:

            # see if this has already happened and a new user was assigned with a diff username

            try:
                u_email = User.objects.get(email__exact=email,
                        username=username)
                authcate_user = u_email
            except User.DoesNotExist, ue:

                pass  # this is a rare case and will have to be handled later
        else:

                # create user somehow and email? (auto_gen username?)

            authcate_user = u
    except User.DoesNotExist, ue:

        from random import choice
        import string

        # random password todo make function

        random_password = ''
        chars = string.letters + string.digits

        for i in range(8):
            random_password = random_password + choice(chars)

        authcate_user = User.objects.create_user(username, email,
                random_password)
        up = UserProfile(authcate_user=True, user=authcate_user)
        up.save()

        # todo :send email with notification

    return authcate_user


