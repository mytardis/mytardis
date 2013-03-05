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

from urllib2 import Request, HTTPError, build_opener, \
    HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, \
    HTTPDigestAuthHandler
from urllib import quote
from urllib2 import URLError
from urlparse import urlparse, urljoin
import os

from django.utils import simplejson

from .base import TransferError, TransferProvider

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
    
    def __init__(self, name, base_url, params):
        TransferProvider.__init__(self, name, base_url)
        self.metadata_supported = False
        self.trust_length = params.get('trust_length', 'False') == 'True'
        self.opener = self._build_opener(params, base_url)

    def _build_opener(self, params, base_url):
        user = params.get('user', '')
        if user:
            realm = params.get('realm', '')
            password = params.get('password', '')
            scheme = params.get('scheme', 'digest')
            password_mgr = HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(realm, base_url, user, password) 
            if scheme == 'basic':
                handler = HTTPBasicAuthHandler(password_mgr)
            elif scheme == 'digest':
                handler = HTTPDigestAuthHandler(password_mgr)
            else:
                raise ValueError('Unknown auth type "%s"' % scheme)
            return build_opener(handler)
        else:
            return build_opener()

    def alive(self):
        try:
            self.opener.open(self.base_url)
            return True
        except URLError:
            return False

    def get_length(self, replica):
        try:
            response = self.opener.open(self.HeadRequest(replica.url))
        except HTTPError as e:
            raise TransferError(e.reason);
        length = response.info().get('Content-length')
        if length is None:
            raise TransferError("No content-length in response")
        try:
            return int(length)
        except TypeError:
            raise TransferError("Content-length is not numeric")
        
    def get_metadata(self, replica):
        if not self.metadata_supported:
            raise NotImplementedError
        try:
            response = self.opener.open(
                self.GetRequest(replica.url + "?metadata"))
            return simplejson.load(response)
        except HTTPError as e:
            raise TransferError(e.reason)
    
    def get_opener(self, replica):
        url = replica.url
        self._check_url(url)

        def getter():
            try:
                return self.opener.open(url)
            except HTTPError as e:
                raise TransferError(e.reason)

        return getter

    def generate_url(self, replica):
        return replica.generate_default_url()

    def put_file(self, source_replica, target_replica):
        self._check_url(target_replica.url)
        try:
            with source_replica.get_file() as f:
                content = f.read()
            request = self.PutRequest(target_replica.url)
            request.add_header('Content-Length', str(len(content)))
            request.add_header('Content-Type', source_replica.datafile.mimetype)
            response = self.opener.open(request, data=content)
        except HTTPError as e:
            raise TransferError(e.reason)

    def remove_file(self, replica):
        self._check_url(replica.url)
        try:
            self.opener.open(self.DeleteRequest(replica.url))
        except HTTPError as e:
            raise TransferError(e.reason)

    def _check_url(self, url):
        if not url.startswith(self.base_url):
            raise TransferError(
                'url %s does not belong to the %s destination (url %s)' % \
                    (url, self.name, self.base_url))
