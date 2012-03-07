
from flexmock import flexmock
from django.test import TestCase
from django.conf import settings

from tardis.apps.sync.consumer_fsm import Complete, InProgress, FailPermanent, \
        CheckingIntegrity, Requested, Ingested
from ..transfer_service import TransferClient, HttpClient, TransferService

class PluggableHttpClient(HttpClient):
    pass

class PluggedTransferClient(TransferClient):
    client_class = PluggableHttpClient

class TCInitialisationTestCase(TestCase):

    def has_function(self, obj, func_name):
        self.assertTrue(hasattr(obj, func_name))
        self.assertTrue(callable(getattr(obj, func_name)))

    def implements_http_client_interface(self, tc):
        self.assertTrue(hasattr(tc, 'client'))
        self.assertIsInstance(tc.client, HttpClient)
        self.has_function(tc.client, 'get')
        self.has_function(tc.client, 'post')


    def testRegularInitialisation(self):
        tc = TransferClient()
        self.implements_http_client_interface(tc)
    
    def testPluggableHttpClient(self):
        tc = PluggedTransferClient()
        self.implements_http_client_interface(tc)
        self.assertEqual(tc.client.__class__, PluggableHttpClient)

def get_synced_exp(url, uid, exp_id):
    exp = flexmock(id=exp_id)
    se = flexmock(provider_url=url, uid=uid, experiment=exp)
    return se

class StubbedHttpClient(HttpClient):

    def post(self,url, headers={}, data = {}):
        response  = flexmock(status=200)
        content = {}
        return (response, content)

class StubbedTransferClient(TransferClient):
    client_class = StubbedHttpClient

class TCTransferTestCase(TestCase):
    
    stored_data = []


    def setUp(self):
        settings.MYTARDIS_SITE_URL='http://www.tardis.com'
        self.se = get_synced_exp('http://www.test.com', 'test_uid', 1)

    def test_true_on_success(self):
        def post(self, url, headers={}, data={}):
            response  = flexmock(status=200)
            content = {}
            return (response, content)
        StubbedHttpClient.post = post
        tc = StubbedTransferClient()
        ret = tc.request_file_transfer(self.se)
        self.assertTrue(ret)

    def test_false_on_fail(self):
    
        for code in [400, 500, 401]:
            def post(self, url, headers={}, data={}):
                response  = flexmock(status=code, reason='my reason')
                content = {}
                return (response, content)

            StubbedHttpClient.post = post
            tc = StubbedTransferClient()
            ret = tc.request_file_transfer(self.se)
            self.assertFalse(ret)
    
    def test_post_data(self):
        def post(self, url, headers={}, data={}):
            TCTransferTestCase.stored_data = data
            response  = flexmock(status=200)
            content = {}
            return (response, content)
        
        StubbedHttpClient.post = post
        tc = StubbedTransferClient()
        ret = tc.request_file_transfer(self.se)
        self.assertTrue(TCTransferTestCase.stored_data)
        self.assertTrue(ret)
        
        data = TCTransferTestCase.stored_data

        self.assertEqual(data['uid'], self.se.uid)
        self.assertTrue('dest_path' in data)
        self.assertTrue('site_settings_url' in data)

        self.assertEqual(data['dest_path'], str(self.se.experiment.id))


def get_json(json_dict):
    import json
    data = json.dumps(json_dict)
    return data

class TransferClientStatusTestCase(TestCase):


    def setUp(self):
        settings.MYTARDIS_SITE_URL='http://www.tardis.com'
        self.se = get_synced_exp('http://www.test.com', 'test_uid', 1)

    def test_in_progress(self):
        def get(self, url, headers={}, data={}):
            TCTransferTestCase.stored_data = data
            response  = flexmock(status=200)
            content = get_json({
                'status':TransferService.TRANSFER_IN_PROGRESS,
                })
            return (response, content)

        StubbedHttpClient.get = get
        self.se.should_receive('save_status')

        tc = StubbedTransferClient()
        status_dict = tc.get_status(self.se)

        self.assertTrue('status' in status_dict)
        self.assertEqual(status_dict['status'], TransferService.TRANSFER_IN_PROGRESS)

    def test_complete(self):
        def get(self, url, headers={}, data={}):
            TCTransferTestCase.stored_data = data
            response  = flexmock(status=200)
            content = get_json({
                'status':TransferService.TRANSFER_COMPLETE,
                })
            return (response, content)

        StubbedHttpClient.get = get
        self.se.should_receive('save_status')

        tc = StubbedTransferClient()
        status_dict = tc.get_status(self.se)

        self.assertTrue('status' in status_dict)
        self.assertEqual(status_dict['status'], TransferService.TRANSFER_COMPLETE)

    def test_invalid(self):
        def get(self, url, headers={}, data={}):
            TCTransferTestCase.stored_data = data
            response  = flexmock(status=200)
            content = get_json({
                'status':TransferService.TRANSFER_BAD_REQUEST,
                'message':'error',
                })
            return (response, content)

        StubbedHttpClient.get = get
        self.se.should_receive('save_status')

        tc = StubbedTransferClient()
        status_dict = tc.get_status(self.se)

        self.assertTrue('status' in status_dict)
        self.assertEqual(status_dict['status'], TransferService.TRANSFER_BAD_REQUEST)
        self.assertTrue('message' in status_dict)

    def test_extra_returns(self):
        def get(self, url, headers={}, data={}):
            TCTransferTestCase.stored_data = data
            response  = flexmock(status=200)
            content = get_json({
                'status':TransferService.TRANSFER_BAD_REQUEST,
                'message':'error',
                })
            return (response, content)

        StubbedHttpClient.get = get
        self.se.should_receive('save_status')

        tc = StubbedTransferClient()
        status_dict = tc.get_status(self.se)

        self.assertTrue('status' in status_dict)
        self.assertEqual(status_dict['status'], TransferService.TRANSFER_BAD_REQUEST)
        self.assertTrue('message' in status_dict)

    def test_unknown_error(self):
        pass

    def test_non_json_content(self):
        pass




class HttpClientTestCase(TestCase):
    pass

