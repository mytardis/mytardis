from django.test import TestCase
from compare import expect
from nose.tools import ok_, eq_
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from tardis.tardis_portal.migration import Destination, Transfer_Provider,\
    Simple_Http_Transfer

class MigrationTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def testDestination(self):
        '''
        Test that Destination instantiation works
        '''
        dest = Destination('test')
        self.assertIsInstance(dest.provider, Transfer_Provider)
        self.assertIsInstance(dest.provider, Simple_Http_Transfer)
        
        with self.assertRaises(RuntimeError):
            dest2 = Destination('unknown')

    def testProvider(self):
        dest = Destination('test').provider
        provider = dest
        datafile = None
        url = provider.generate_url(datafile)
        provider.transfer_file(datafile, url)

class TestServer(HTTPServer):
    def __init__():
        HTTPServer.__init__(('127.0.0.1', 8181), TestRequestHandler)

class TestRequestHandler(BaseHTTPRequestHandler):
    def do_GET():
        pass
    
    def do_POST():
        pass
