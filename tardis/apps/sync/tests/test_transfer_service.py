from flexmock import flexmock
from django.test import TestCase
from django.conf import settings
import time

from ..transfer_service import TransferClient, HttpClient, TransferService

def get_synced_exp(url, uid, exp_id):
    exp = flexmock(id=exp_id)
    se = flexmock(provider_url=url, uid=uid, experiment=exp)
    return se

class TransferServiceTestCase(TestCase):
    def setUp(self):
        self.se = get_synced_exp('http://www.test.com', 'test_uid', 1)

    def testGetStatus(self):
        rv = (TransferService.TRANSFER_COMPLETE, time.time(), {})
        mock = flexmock()
        mock.should_receive('get_status').and_return(rv)
        ts = TransferService(manager=mock)
        status = ts.get_status('tardis.1')
        self.assertEqual(status['status'], TransferService.TRANSFER_COMPLETE)
        self.assertIn('human_status', status)
        self.assertIn('timestamp', status)
        status['human_status'].lower().index('complete')

