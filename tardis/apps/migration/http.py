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
#    * Neither the name of the <organization> nor the
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

from urllib2 import Request, urlopen, HTTPError
from urlparse import urlparse
import os

from django.utils import simplejson

from .base import MigrationError, MigrationProviderError, TransferProvider

class SimpleHttpTransfer(TransferProvider):
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
    
    def __init__(self, name, base_url, metadata_supported=False):
        TransferProvider.__init__(self, name)
        self.base_url = base_url
        self.metadata_supported = False

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
        with datafile.get_file() as f:
            content = f.read()
        request = self.PutRequest(url)
        request.add_header('Content-Length', str(len(content)))
        request.add_header('Content-Type', datafile.mimetype)
        response = urlopen(request, data=content)
    
    def remove_file(self, url):
        self._check_url(url)
        urlopen(self.DeleteRequest(url))

    def _check_url(self, url):
        if url.find(self.base_url) != 0:
            raise MigrationProviderError(('The url (%s) does not belong to' \
                                ' the %s destination') % (url, self.name))

