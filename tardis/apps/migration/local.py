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

from urllib2 import Request, HTTPError
from urllib import quote
from urlparse import urlparse, urljoin
import os

from django.utils import simplejson

from .base import MigrationError, MigrationProviderError, TransferProvider

class LocalTransfer(TransferProvider):
    def __init__(self, name, base_url, opener, metadata_supported=False):
        TransferProvider.__init__(self, name)
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        self.base_url = base_url
        self.metadata_supported = False
        self.opener = opener

    def get_length(self, url):
        filename = self._url_to_filename(url)
        raise Exception('tbd')
        
    def get_metadata(self, url):
        filename = self._url_to_filename(url)
        raise Exception('tbd')
    
    def get_file(self, url):
        filename = self._url_to_filename(url)
        raise Exception('tbd')
    
    def generate_url(self, replica):
        url = urlparse(replica.url)
        if url.scheme == '' or url.scheme == 'file':
            return urljoin(self.base_url, quote(url.path))
        raise MigrationProviderError("Cannot generate a URL from '%s'" \
                                         % replica.url)

    def url_matches(self, url):
        return url.startswith(self.base_url)
    
    def put_file(self, replica, url):
        filename = self._url_to_filename(url)
        raise Exception('tbd')
    
    def remove_file(self, url):
        filename = self._url_to_filename(url)
        raise Exception('tbd')

    def _url_to_filename(self, url):
        if not url.startswith(self.base_url):
            raise MigrationProviderError(('The url (%s) does not belong to' \
                                ' the %s destination') % (url, self.name))
        return ''

