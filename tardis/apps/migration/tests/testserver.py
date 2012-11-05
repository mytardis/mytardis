#
# Copyright (c) 2012, Centre for Microscopy and Microanalysis
#   (University of Queensland, Australia)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the University of Queensland nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
#

from SimpleHTTPServer import SimpleHTTPRequestHandler
import BaseHTTPServer, SocketServer, threading, hashlib

from django.utils import simplejson

class SimpleHttpTestServer:
    '''
    A test destination server that is compatible with the SimpleHttpProvider.
    '''

    class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_GET(self, outputBody=True):
            (path, query) = self._splitPath()
            try:
                (data, length, mimetype) = self.server.store[path] 
            except:
                self.send_error(404)
                return
            if query:
                if query == 'metadata' and self.server.allowQuery:
                    data = self._createHashResponse(data)
                    length = len(data)
                    mimetype = 'application/json'
                else:
                    self.send_error(400)
                    return
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
            (path, query) = self._splitPath()
            if query:
                self.send_error(400)
            try:
                self.server.store.pop(path) 
                self.send_response(200)
            except:
                self.send_error(404)

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

    def __init__(self, allowQuery=True):
        self.handler = self.RequestHandler
        self.allowQuery = allowQuery

    def start(self):
        server = self.ThreadedTCPServer(('127.0.0.1', self.getPort()),
                                        self.handler)
        server.allowQuery = self.allowQuery
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

