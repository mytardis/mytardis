from urllib2 import Request, urlopen, HTTPError
from urlparse import urlparse

from tardis.apps.migration import TransferProvider, MigrationProviderError, \
    SimpleHttpTransfer


class WebDAVTransfer(SimpleHttpTransfer):
    class HeadRequest(Request):
        def get_method(self):
            return 'HEAD'
    
    class PutRequest(Request):
        def get_method(self):
            return 'PUT'
    
    class GetRequest(Request):
        def get_method(self):
            return 'GET'
    
    class DeleteRequest(Request):
        def get_method(self):
            return 'DELETE'
    
    class MkcolRequest(Request):
        def get_method(self):
            return 'MKCOL'
    
    def __init__(self, name, base_url, metadata_supported=False):
        SimpleHttpTransfer.__init__(self, name, base_url)

    def get_metadata(self, url):
        raise NotImplementedError
    
    def put_file(self, datafile, url):
        self._check_url(url)
        self._create_parent_collections(url)
        super(WebDAVTransfer, self).put_file(datafile, url)

    def _create_parent_collections(self, url):
        path = url[len(self.base_url):].split('/')
        if len(path) > 1:
            partial = self.base_url
            for part in path[0:len(path) - 1]:
                partial += part
                try:
                    request = self.MkcolRequest(partial)
                    response = urlopen(request)
                except HTTPError as e:
                    if e.code == 405 or e.code == 301:
                        pass
                partial += '/'
        
