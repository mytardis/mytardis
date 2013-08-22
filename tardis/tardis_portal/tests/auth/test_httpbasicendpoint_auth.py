'''
Created on Dec 15, 2011

@author: Tim Dettrick <t.dettrick@uq.edu.au>
'''
from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User, Group
import base64
import urllib2
import tempfile
import BaseHTTPServer
import SocketServer
import threading
from flexmock import flexmock, flexmock_teardown
from nose.tools import ok_, eq_

from tardis.tardis_portal.auth.httpbasicendpoint_auth import HttpBasicEndpointAuth

class HttpBasicEndpointAuthTestCase(TestCase):

    class TestWebServer:
        '''
        Utility class for running a test web server with a given handler.
        '''

        class ThreadedTCPServer(SocketServer.ThreadingMixIn, \
                                BaseHTTPServer.HTTPServer):
            pass

        def __init__(self, handler):
            self.handler = handler

        def start(self):
            server = self.ThreadedTCPServer(('127.0.0.1', 0), self.handler)
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            self.server = server
            return server.socket.getsockname()

        def getUrl(self):
            return 'http://%s:%d/' % self.server.socket.getsockname()

        def stop(self):
            self.server.shutdown()

    class QuietBaseHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
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
            if base64.b64decode(creds) != "testuser:password":
                return False
            return True

        def getCode(self):
            return (499, "Not implemented")

        def do_GET(self):
            if not self._isAuthorized():
                self.send_response(401, 'Unauthorized')
                self.send_header('WWW-Authenticate', 'Basic realm="Test"')
                self.end_headers()
                return
            self.send_response(*self.getCode())


    class Always200Handler(QuietBaseHTTPRequestHandler):

        def getCode(self):
            return (200, 'OK')


    class Always403Handler(QuietBaseHTTPRequestHandler):

        def getCode(self):
            return (403, 'Forbidden')


    def setUp(self):
        self.mock_endpoint = 'http://test.example/login'

    def tearDown(self):
        flexmock_teardown()

    '''
    Test our test web-server (we need it for the later tests).
    '''
    def testTestWebserver(self):
        server = self.TestWebServer(self.Always200Handler)
        host, port = server.start()
        assert host == '127.0.0.1'
        assert port > 0 and port < pow(2,16)
        assert server.getUrl() == 'http://127.0.0.1:%d/' % port
        try:
            urllib2.urlopen(server.getUrl())
            ok_(False, "We expected an error fetching this url.")
        except urllib2.HTTPError as e:
            eq_(e.code, 401)
        request = urllib2.Request(server.getUrl())
        base64string = base64.encodestring('%s:%s' % ('testuser', 'password'))\
            .replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        try:
            urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            assert False # We should not have got an error
        server.stop()

    def testAllowOnSuccess(self):
        username = 'testuser'
        request = RequestFactory().post('/login', { 'username': username,
                                                   'password': 'password'})
        # A "successful" mock OpenerDirector
        result = tempfile.TemporaryFile(mode='r')
        mockOpener = flexmock(urllib2.OpenerDirector(), open = result)
        # Stub out user object retrieval & creation
        mockUserDao = flexmock(User.objects)
        mockUserDao.should_receive('get').and_raise(User.DoesNotExist())
        mockUserDao.should_call('create_user').with_args(username, '')\
            .at_least.once
        auth = HttpBasicEndpointAuth(mockOpener,endpoint=self.mock_endpoint)
        self._checkResult(auth.authenticate(request),username)

    def testDenyOnFailure(self):
        request = RequestFactory().post('/login', { 'username': 'testuser',
                                                   'password': 'password'})
        # A "successful" mock OpenerDirector
        error403 = urllib2.HTTPError(self.mock_endpoint, 403, "Forbidden", {}, None)
        mockOpener = flexmock(urllib2.OpenerDirector())
        mockOpener.should_receive('open').and_raise(error403)
        auth = HttpBasicEndpointAuth(mockOpener,endpoint=self.mock_endpoint)
        eq_(auth.authenticate(request), None)

    def testAcceptFromRealEndpoint(self):
        username = 'testuser'
        request = RequestFactory().post('/login', { 'username': username,
                                                   'password': 'password'})
        server = self.TestWebServer(self.Always200Handler)
        server.start()
        auth = HttpBasicEndpointAuth(endpoint=server.getUrl())
        # Stub out user object retrieval & creation
        mockUserDao = flexmock(User.objects)
        mockUserDao.should_receive('get').and_raise(User.DoesNotExist())
        mockUserDao.should_call('create_user').with_args(username, '')\
            .at_least.once
        # Ditto for group object retrieval
        group = Group.objects.create(name='test-group')
        group.save()
        mockGroupDao = flexmock(Group.objects)
        mockGroupDao.should_receive('get').with_args(name='test-group')\
            .and_return(group).at_least.once
        mockGroupDao.should_receive('get').with_args(name='unknown-group')\
            .and_raise(Group.DoesNotExist)

        result = auth.authenticate(request)
        server.stop()
        self._checkResult(result, username)

    def testDenyFromRealEndpoint(self):
        request = RequestFactory().post('/login', { 'username': 'testuser',
                                                   'password': 'password'})
        server = self.TestWebServer(self.Always403Handler)
        server.start()
        auth = HttpBasicEndpointAuth(endpoint=server.getUrl())
        result = auth.authenticate(request)
        server.stop()
        assert result == None

    def testCanHandlePreviousUser(self):
        username = 'testuser'
        request = RequestFactory().post('/login', { 'username': username,
                                                   'password': 'password'})
        # A "successful" mock OpenerDirector
        result = tempfile.TemporaryFile(mode='r')
        mockOpener = flexmock(urllib2.OpenerDirector(), open = result)
        # Stub out user object retrieval & creation
        mockUserDao = flexmock(User.objects)
        mockUserDao.should_receive('get')\
            .and_return(User(username=username))\
            .at_least.once
        mockUserDao.should_call('create_user')\
            .with_args(username, '')\
            .never
        auth = HttpBasicEndpointAuth(mockOpener,endpoint=self.mock_endpoint)
        self._checkResult(auth.authenticate(request),username)

    def _checkResult(self, result, username):
        assert not isinstance(result, dict)
        assert isinstance(result, User)
        eq_(result.username, username)
