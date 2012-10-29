from urllib2 import Request, urlopen, HTTPError
from urlparse import urlparse
import simplejson, os

from tardis.apps.migration import TransferProvider, MigrationProviderError

class WebDAVTransfer(TransferProvider):
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
    
    def __init__(self, name, base_url, metadata_supported=False,
                 create_parents=False):
        TransferProvider.__init__(self, name)
        self.base_url = base_url
        self.metadata_supported = False
        self.create_parents = create_parents

    def get_length(self, url):
        self._check_url(url)
        response = urlopen(self.HeadRequest(url))
        length = response.info().get('Content-length')
        if length is None:
            raise MigrationProviderError("No content-length in response")
        try:
            return int(length)
        except TypeError:
            raise MigrationProviderError("Content-length is not numeric")
        
    def get_metadata(self, url):
        if not self.metadata_supported:
            raise NotImplementedError
        self._check_url(url)
        response = urlopen(self.GetRequest(url + "?metadata"))
        return simplejson.load(response)
    
    def get_file(self, url):
        self._check_url(url)
        response = urlopen(self.GetRequest(url))
        return response.read()
    
    def generate_url(self, datafile):
        url = urlparse(datafile.url)
        if url.scheme == '' or url.scheme == 'file':
            return self.base_url + url.path
        raise MigrationProviderError("Cannot generate a URL from '%s'" \
                                         % datafile.url)
    
    def put_file(self, datafile, url):
        self._check_url(url)
        if self.create_parents:
            self._create_parent_collections(url)
        with open(datafile.filename) as f:
            content = f.read()
        request = self.PutRequest(url)
        request.add_header('Content-Length', str(len(content)))
        request.add_header('Content-Type', datafile.mimetype)
        response = urlopen(request, data=content)
    
    def remove_file(self, url):
        self._check_url(url)
        urlopen(self.DeleteRequest(url))

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
        
    def _check_url(self, url):
        if url.find(self.base_url) != 0:
            raise MigrationProviderError(('The url (%s) does not belong to' \
                                ' the %s destination') % (url, self.name))

