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

from urllib2 import Request, urlopen, HTTPError
from urlparse import urlparse

from tardis.apps.migration import TransferProvider, MigrationProviderError, \
    SimpleHttpTransfer


class WebDAVTransfer(SimpleHttpTransfer):
    
    class MkcolRequest(Request):
        def get_method(self):
            return 'MKCOL'
    
    def __init__(self, name, base_url, opener, metadata_supported=False):
        SimpleHttpTransfer.__init__(self, name, base_url, opener)

    def get_metadata(self, url):
        raise NotImplementedError
    
    def put_file(self, replica, url):
        self._check_url(url)
        self._create_parent_collections(url)
        super(WebDAVTransfer, self).put_file(replica, url)

    def _create_parent_collections(self, url):
        path = url[len(self.base_url):].split('/')
        if len(path) > 1:
            partial = self.base_url
            for part in path[0:len(path) - 1]:
                partial += part
                try:
                    request = self.MkcolRequest(partial)
                    response = self.opener.open(request)
                except HTTPError as e:
                    if e.code == 405 or e.code == 301:
                        pass
                partial += '/'
        
