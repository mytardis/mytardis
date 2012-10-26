from SimpleHTTPServer import SimpleHTTPRequestHandler
import BaseHTTPServer, SocketServer, threading, hashlib, simplejson

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

