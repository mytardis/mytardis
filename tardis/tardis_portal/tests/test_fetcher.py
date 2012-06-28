from django.test import TestCase
from compare import expect
from nose.tools import ok_, eq_

from SimpleHTTPServer import SimpleHTTPRequestHandler
import BaseHTTPServer, base64, os, SocketServer, threading, urllib2

from tardis.tardis_portal.fetcher import get_privileged_opener

class TestWebServer:
    '''
    Utility class for running a test web server with a given handler.
    '''

    class QuietSimpleHTTPRequestHandler(SimpleHTTPRequestHandler):
        '''
        Simple subclass that only prints output to STDOUT, not STDERR
        '''
        def log_message(self, msg, *args):
            print msg % args

        def _isAuthorized(self):
            if self.headers.getheader('Authorization') == None:
                return False
            t, creds = self.headers.getheader('Authorization').split(" ")
            if t != "Basic":
                return False
            if base64.b64decode(creds) != "username:password":
                return False
            return True

        def do_GET(self):
            if not self._isAuthorized():
                self.send_response(401, 'Unauthorized')
                self.send_header('WWW-Authenticate', 'Basic realm="Test"')
                self.end_headers()
                return
            SimpleHTTPRequestHandler.do_GET(self)

    class ThreadedTCPServer(SocketServer.ThreadingMixIn, \
                            BaseHTTPServer.HTTPServer):
        pass

    def __init__(self):
        self.handler = self.QuietSimpleHTTPRequestHandler

    def start(self):
        server = self.ThreadedTCPServer(('127.0.0.1', self.getPort()),
                                        self.handler)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
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

class PrivilegedOpenerTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.priorcwd = os.getcwd()
        os.chdir(os.path.dirname(__file__))
        cls.server = TestWebServer()
        cls.server.start()
        pass

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.priorcwd)
        cls.server.stop()

    def testCredentials(self):
        '''
        Test that the walker manages credentials.
        '''
        address = 'http://localhost:%d/test.jpg' % \
                                (TestWebServer.getPort())
        # We shouldn't be able to get the file without credentials
        try:
            urllib2.urlopen(address)
            ok_(False, 'Should have thrown error')
        except urllib2.HTTPError:
            pass
        # We should be able to get it with the provided credentials
        try:
            f = get_privileged_opener().open(address)
            eq_(f.getcode(), 200, 'Should have been: "200 OK"')
        except urllib2.HTTPError:
            ok_(False, 'Should not have thrown error')
        pass