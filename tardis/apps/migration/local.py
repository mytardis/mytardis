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
from urllib import quote, unquote
from urlparse import urlparse, urljoin
import os

from django.utils import simplejson
from django.conf import settings
from tardis.tardis_portal.staging import stage_replica

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
        return os.path.getsize(filename)
        
    def get_metadata(self, url):
        filename = self._url_to_filename(url)
        raise Exception('tbd')
    
    def get_file(self, url):
        filename = self._url_to_filename(url)
        raise Exception('tbd')
    
    def generate_url(self, replica):
        return replica.generate_default_url()

    def url_matches(self, url):
        return url.startswith(self.base_url)
    
    def put_file(self, source_replica, target_replica):
        target_replica.url = source_replica.url
        if not stage_replica(target_replica):
            raise MigrationProviderError(
                'Staging from url %s to local replica failed' % 
                source_replica.url)
    
    def remove_file(self, url):
        filename = self._url_to_filename(url)
        os.remove(filename)

    def _url_to_filename(self, url):
        print '_url_to_filename: %s %s\n' % (url, self.base_url)
        # This is crude and possibly fragile.
        if not url.startswith(self.base_url):
            raise MigrationProviderError(('The url (%s) does not belong to' \
                                ' the %s destination (url %s)') % \
                                             (url, self.name, self.base_url))
        parts = urlparse(url)
        if parts.scheme == 'file':
            return unquote('/%s/%s' % (parts.netloc, parts.path))
        else:
            return settings.FILE_STORE_PATH + url[len(base_url):]

