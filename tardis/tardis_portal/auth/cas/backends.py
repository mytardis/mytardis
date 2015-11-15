"""CAS authentication backend"""

import urllib
from urllib import urlencode, urlopen
from urlparse import urljoin

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Permission
from tardis.tardis_portal.auth.cas.models import User, Tgt, PgtIOU
from tardis.tardis_portal.auth.cas import CAS
from tardis.tardis_portal.auth.utils import configure_user

import logging

logger = logging.getLogger(__name__)

__all__ = ['CASBackend']



def _verify_cas1(ticket, service):
    """Verifies CAS 1.0 authentication ticket.

    Returns username on success and None on failure.
    """

    params = {'ticket': ticket, 'service': service}
    url = (urljoin(settings.CAS_SERVER_URL, 'validate') + '?' +
           urlencode(params))
    page = urlopen(url)
    try:
        verified = page.readline().strip()
        if verified == 'yes':
            return page.readline().strip(), None
        else:
            return None, None
    finally:
        page.close()


def _verify_cas2(ticket, service):
    """Verifies CAS 2.0+ XML-based authentication ticket.

    Returns username on success and None on failure.
    """

    try:
        from xml.etree import ElementTree
    except ImportError:
        from elementtree import ElementTree

    if settings.CAS_PROXY_CALLBACK:
        params = {'ticket': ticket, 'service': service, 'pgtUrl': settings.CAS_PROXY_CALLBACK}
    else:
        params = {'ticket': ticket, 'service': service}

    url = (urljoin(settings.CAS_SERVER_URL, 'proxyValidate') + '?' +
           urllib.urlencode(params))

    logger.debug("url = " + url)
    page = urllib.urlopen(url)
    response = page.read()
    tree = ElementTree.fromstring(response)
    page.close()

    if tree.find(CAS + 'authenticationSuccess') is not None:
        username = tree.find(CAS + 'authenticationSuccess/' + CAS + 'user').text
        pgtIouIdElement = tree.find(CAS + 'authenticationSuccess/' + CAS + 'proxyGrantingTicket')
        pgtIouId = pgtIouIdElement.text if pgtIouIdElement is not None else None

        if pgtIouId:
            pgtIou = PgtIOU.objects.get(pgtIou=pgtIouId)
            try:
                tgt = Tgt.objects.get(username=username)
                tgt.tgt = pgtIou.tgt
                tgt.save()
            except ObjectDoesNotExist:
                Tgt.objects.create(username=username, tgt=pgtIou.tgt)

            pgtIou.delete()
        return username, tree
    else:
        return None, tree


def verify_proxy_ticket(ticket, service):
    """Verifies CAS 2.0+ XML-based proxy ticket.

    Returns username on success and None on failure.
    """

    try:
        from xml.etree import ElementTree
    except ImportError:
        from elementtree import ElementTree

    params = {'ticket': ticket, 'service': service}

    url = (urljoin(settings.CAS_SERVER_URL, 'proxyValidate') + '?' +
           urlencode(params))

    page = urlopen(url)

    try:
        response = page.read()
        tree = ElementTree.fromstring(response)
        if tree[0].tag.endswith('authenticationSuccess'):
            username = tree[0][0].text
            proxies = []
            if len(tree[0]) > 1:
                for element in tree[0][1]:
                    proxies.append(element.text)
            return {"username": username, "proxies": proxies}
        else:
            return None
    finally:
        page.close()

_PROTOCOLS = {'1': _verify_cas1, '2': _verify_cas2}

if settings.CAS_VERSION not in _PROTOCOLS:
    raise ValueError('Unsupported CAS_VERSION %r' % settings.CAS_VERSION)

_verify = _PROTOCOLS[settings.CAS_VERSION]

_CAS_USER_DETAILS_RESOLVER = getattr(settings, 'CAS_USER_DETAILS_RESOLVER', None)


class CASBackend(object):
    """CAS authentication backend"""

    def authenticate(self, ticket, service):
        """Verifies CAS ticket and gets or creates User object
           NB: Use of PT to identify proxy
        """
        username, authentication_response = _verify(ticket, service)
        if not username:
            return None

        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_unusable_password()
            user.save()
            #user.user_permissions.add(Permission.objects.get(codename='add_experiment'))
            #user.user_permissions.add(Permission.objects.get(codename='change_experiment'))
            #user.user_permissions.add(Permission.objects.get(codename='change_group'))
            #user.user_permissions.add(Permission.objects.get(codename='change_userauthentication'))
            #user.user_permissions.add(Permission.objects.get(codename='change_objectacl'))
            #user.user_permissions.add(Permission.objects.get(codename='change_dataset'))
            #user.user_permissions.add(Permission.objects.get(codename='add_dataset_file'))
            configure_user(user)

        if authentication_response and _CAS_USER_DETAILS_RESOLVER:
            _CAS_USER_DETAILS_RESOLVER(user, authentication_response)

        user.save()
        return user

    def get_user(self, user_id):
        """Retrieve the user's entry in the User model if it exists"""

        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

