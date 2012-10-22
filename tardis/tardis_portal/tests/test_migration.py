from django.test import TestCase
from compare import expect
from threading import Thread
import logging
from tempfile import NamedTemporaryFile
from nose.tools import ok_, eq_

from SimpleHTTPServer import SimpleHTTPRequestHandler
import BaseHTTPServer, base64, os, SocketServer, threading, urllib2

from tardis.tardis_portal.fetcher import get_privileged_opener

from tardis.tardis_portal.migration import Destination, Transfer_Provider,\
    Simple_Http_Transfer
from tardis.tardis_portal.models import Dataset_File, Dataset, Experiment

class MigrationTestCase(TestCase):

    def setUp(self):
        self.dummy_dataset = Dataset()
        self.dummy_dataset.save()
        self.server = TestServer()
        self.server.start()

    def tearDown(self):
        self.dummy_dataset.delete()
        self.server.stop()

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
        datafile = self._generate_datafile("/1/2/3", "Hi mum")
        url = provider.generate_url(datafile)
        provider.transfer_file(datafile, url)

    def _generate_datafile(self, path, content):
        file = NamedTemporaryFile(delete=False)
        file.write(content)
        file.close()
        datafile = Dataset_File()
        datafile.url = path
        datafile.mimetype = "application/unspecified"
        datafile.filename = file.name
        datafile.dataset_id = self.dummy_dataset.id
        datafile.size = str(len(content))
        datafile.save()
        return datafile


class TestServer:
    '''
    Utility class for running a test web server with a given handler.
    '''

    class TestRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_GET(self):
            pass
    
        def do_POST(self):
            pass

        def do_PUT(self):
            length = int(self.headers.getheader('Content-Length'))
            mimetype = self.headers.getheader('Content-Type')
            data = self.rfile.read(length)
            self.server.store[self.path] = (data, length, mimetype) 
            self.send_response(200)

        def do_DELETE(self):
            pass
            
        def do_HEAD(self):
            pass

        def log_message(self, msg, *args):
            print(msg % args)

    class ThreadedTCPServer(SocketServer.ThreadingMixIn, \
                            BaseHTTPServer.HTTPServer):
        pass

    def __init__(self):
        self.handler = self.TestRequestHandler

    def start(self):
        server = self.ThreadedTCPServer(('127.0.0.1', self.getPort()),
                                        self.handler)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        server.store = {}
        self.server = server
        return server.socket.getsockname()

    def getUrl(self):
        return 'http://%s:%d/' % self.server.socket.getsockname()

    @classmethod
    def getPort(cls):
        return 4272

    def stop(self):
        self.server.shutdown()
        self.server.socket.close()

