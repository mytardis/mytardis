from StringIO import StringIO
import urllib
from django.conf import settings
from django.test import TestCase

from tardis.tardis_portal.auth.cas.backends import _verify_cas2
from tardis.tardis_portal.auth.cas.models import PgtIOU, Tgt

__author__ = 'sannies'

def dummyUrlOpenNoProxyGrantingTicket(url):
    return StringIO(
        '<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas"><cas:authenticationSuccess><cas:user>sannies</cas:user><cas:attributes><cas:attraStyle>Jasig</cas:attraStyle><cas:merchant>sannies</cas:merchant><cas:userServerUrl>http://localhost:8080/user-authorization-adapter/</cas:userServerUrl><cas:firstname></cas:firstname><cas:lastname></cas:lastname><cas:is_superuser>True</cas:is_superuser><cas:is_staff>True</cas:is_staff><cas:ROLES>ROLE_SUPERUSER</cas:ROLES><cas:ROLES>ROLE_STAFF</cas:ROLES><cas:ROLES>ROLE_USER</cas:ROLES><cas:ROLES>ROLE_MERCHANT</cas:ROLES><cas:playReadyLicenseAcquisitionUiUrl>http://www.drmtoday.com/</cas:playReadyLicenseAcquisitionUiUrl><cas:email>Sebastian.Annies@castlabs.com</cas:email></cas:attributes></cas:authenticationSuccess></cas:serviceResponse>')


def dummyUrlOpenWithProxyGrantingTikcet(url):
    return StringIO(
        '<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas"><cas:authenticationSuccess><cas:user>sannies</cas:user><cas:attribute name="attraStyle" value="Name-Value"/><cas:attribute name="is_staff" value="True"/><cas:attribute name="is_active" value="True"/><cas:attribute name="email" value="root@example.com"/><cas:proxyGrantingTicket>PGTIOU-NUYny6RiAfHBsuWq270m3l1kgPTjEOCexpowQV9ZJDrh8cGKzb</cas:proxyGrantingTicket></cas:authenticationSuccess></cas:serviceResponse>')


class backendTest(TestCase):
    def test_verify_cas2_no_pgt(self):
        urllib.urlopen = dummyUrlOpenNoProxyGrantingTicket
        settings.CAS_PROXY_CALLBACK = None
        user, authentication_response = _verify_cas2('ST-jkadfhjksdhjkfh', 'http://dummy')
        self.assertEqual('sannies', user)

    def test_verify_cas2_with_pgt(self):
        urllib.urlopen = dummyUrlOpenWithProxyGrantingTikcet
        #st = ServiceTicket.objects.create();
        tgt = Tgt.objects.create(username='sannies')
        PgtIOU.objects.create(tgt=tgt, pgtIou='PGTIOU-NUYny6RiAfHBsuWq270m3l1kgPTjEOCexpowQV9ZJDrh8cGKzb')

        settings.CAS_PROXY_CALLBACK = "http://dummy2"
        prior = PgtIOU.objects.count()
        user, authentication_response = _verify_cas2('ST-jkadfhjksdhjkfh', 'http://dummy')
        self.assertEqual(prior - 1, PgtIOU.objects.count()) # the pgtiou should be used up and deleted
        self.assertEqual('sannies', user)
