
from flexmock import flexmock
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from ..transfer_service import TransferClient

class ProviderViewsTestCase(TestCase):
    def setUp(self):
        self.tc_mock = flexmock()
        flexmock(TransferClient).new_instances(self.tc_mock)
        # Trick request.is_secure()
        self.kwargs = { "wsgi.url_scheme": "https" }

    def testTransferStatusNoSSL(self):
        self.tc_mock.should_receive('get_status').never
        resp = self.client.get(reverse('sync-transfer-status', args=['tardis.1']))
        self.assertEqual(resp.status_code, 404)

    def testTransferStatusNoAuth(self):
        self.tc_mock.should_receive('get_status').never
        resp = self.client.get(reverse('sync-transfer-status', args=['tardis.1']), **self.kwargs)
        self.assertEqual(resp.status_code, 403)

    def testTransferStatusInvalidAuth(self):
        self.tc_mock.should_receive('get_status').never
        kwargs = { 'HTTP_X_MYTARDIS_KEY': 'wrong_client_key' }
        kwargs.update(self.kwargs)
        resp = self.client.get(reverse('sync-transfer-status', args=['tardis.1']), **kwargs)
        self.assertEqual(resp.status_code, 403)
        resp.content

    def testTransferStatusCorrectAuth(self):
        self.tc_mock.should_receive('get_status').and_return({})
        kwargs = { 'HTTP_X_MYTARDIS_KEY': 'valid_client_key' }
        kwargs.update(self.kwargs)
        resp = self.client.get(reverse('sync-transfer-status', args=['tardis.1']), **kwargs)
        self.assertEqual(resp.status_code, 200)

