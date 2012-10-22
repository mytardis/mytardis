from django.test import TestCase
from compare import expect
from threading import Thread
import logging
import simplejson
import hashlib
from tempfile import NamedTemporaryFile
from nose.tools import ok_, eq_

from SimpleHTTPServer import SimpleHTTPRequestHandler
import BaseHTTPServer, base64, os, SocketServer, threading, urllib2
from urllib2 import HTTPError

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
        self.assertEquals(url, 'http://127.0.0.1:4272/data/1/2/3')
        provider.put_file(datafile, url)

        self.assertEqual(provider.get_file(url), "Hi mum")
        with self.assertRaises(RuntimeError):
            provider.get_file('https://127.0.0.1:4272/data/1/2/4')
        with self.assertRaises(HTTPError):
            provider.get_file('http://127.0.0.1:4272/data/1/2/4')

        self.assertEqual(provider.get_length(url), 6)
        with self.assertRaises(RuntimeError):
            provider.get_length('https://127.0.0.1:4272/data/1/2/4')
        with self.assertRaises(HTTPError):
            provider.get_length('http://127.0.0.1:4272/data/1/2/4')

        self.assertEqual(provider.get_hashes(url),
                         {'sha512sum' : '2274cc8c16503e3d182ffaa835c543bce27' +
                          '8bc8fc971f3bf38b94b4d9db44cd89c8f36d4006e5abea29b' +
                          'c05f7f0ea662cb4b0e805e56bbce97f00f94ea6e6498', 
                          'md5sum' : '3b6b51114c3d0ad347e20b8e79765951',
                          'length' : 6})
        with self.assertRaises(RuntimeError):
            provider.get_hashes('https://127.0.0.1:4272/data/1/2/4')
        with self.assertRaises(HTTPError):
            provider.get_hashes('http://127.0.0.1:4272/data/1/2/4')
            

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
        def do_GET(self, outputBody=True):
            (path, query) = self._splitPath()
            try:
                (data, length, mimetype) = self.server.store[path] 
            except:
                self.send_error(404)
                return
            if query:
                if query == 'hashes':
                    data = self._createHashResponse(data)
                    length = len(data)
                    mimetype = 'application/json'
                else:
                    self.send_error(400)
            self.send_response(200)
            self.send_header('Content-length', str(length))
            self.send_header('Content-type', mimetype)
            self.end_headers()
            if outputBody:
                self.wfile.write(data)
    
        def do_PUT(self):
            length = int(self.headers.getheader('Content-Length'))
            mimetype = self.headers.getheader('Content-Type')
            data = self.rfile.read(length)
            self.server.store[self.path] = (data, length, mimetype) 
            self.send_response(200)

        def do_DELETE(self):
            pass

        def do_HEAD(self):
            self.do_GET(outputBody=False)

        def log_message(self, msg, *args):
            print(msg % args)

        def _splitPath(self):
            tmp = self.path.split('?', 1)
            if len(tmp) == 2:
                return (tmp[0], tmp[1])
            else:
                return (tmp[0], None)

        def _createHashResponse(self, data):
            m = hashlib.sha512()
            m.update(data)
            sha512 = m.hexdigest()
            m = hashlib.md5()
            m.update(data)
            md5 = m.hexdigest()
            return simplejson.dumps({'sha512sum' : sha512, 
                                     'md5sum' : md5,
                                     'length' : len(data)})

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

