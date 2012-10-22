from django.test import TestCase
from compare import expect
from threading import Thread
import logging
from tempfile import NamedTemporaryFile
from nose.tools import ok_, eq_
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from tardis.tardis_portal.migration import Destination, Transfer_Provider,\
    Simple_Http_Transfer
from tardis.tardis_portal.models import Dataset_File, Dataset, Experiment

class MigrationTestCase(TestCase):

    def setUp(self):
        self.dummy_dataset = Dataset()
        self.dummy_dataset.save()
        self.server = ServerThread()
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


class ServerThread(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.httpd = TestServer()

    def run(self):
        self.httpd.serve_forever(poll_interval=0.01)

    def stop(self):
        self.httpd.shutdown()
        self.httpd.socket.close()
        self.join()

class TestServer(HTTPServer):
    def __init__(self):
        HTTPServer.__init__(self, ('127.0.0.1', 8181), TestRequestHandler)

class TestRequestHandler(BaseHTTPRequestHandler):
    def do_GET():
        pass
    
    def do_POST():
        pass
