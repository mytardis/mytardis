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
from os import path
from contextlib import closing

from django.utils import simplejson
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.core.exceptions import SuspiciousOperation

from tardis.tardis_portal.util import generate_file_checksums

from .base import MigrationError, MigrationProviderError, TransferProvider

class BaseLocalTransfer(TransferProvider):
    def __init__(self, name, base_url, params):
        TransferProvider.__init__(self, name, base_url)
        self.trust_length = params.get('trust_length', 'False') == 'True'
        self.metadata_supported = False

        # Subclasses need to set these appropriately
        self.storage = None
        self.base_path = None

    def alive(self):
        return True

    def get_length(self, replica):
        filename = self._uri_to_filename(replica.url)
        try:
            return self.storage.size(filename)
        except OSError as e:
            raise MigrationProviderError(e.strerror)
        
    def get_metadata(self, replica):
        filename = self._uri_to_filename(replica.url)
        with self.storage.open(filename, 'r') as f:
            try:
                md5sum, sha512sum, size, _ = generate_file_checksums(f, None)
            except OSError as e:
                raise MigrationProviderError(e.strerror)
            return {'md5sum': md5sum,
                    'sha512sum': sha512sum,
                    'length': str(size)}
    
    def get_opener(self, replica):
        path = self._uri_to_filename(replica.url)
        def getter():
            try:
                return self.storage.open(path)
            except OSError as e:
                raise MigrationProviderError(e.strerror)
        return getter
   
    def generate_url(self, replica):
        return replica.generate_default_url()
    
    def put_file(self, source_replica, target_replica):
        datafile = target_replica.datafile
        with TemporaryUploadedFile(datafile.filename, 
                                   None, None, None) as tf:
            with closing(source_replica.get_file()) as rf:
                tf.file.write(rf.read())
            tf.file.flush()
            dspath = datafile.dataset.get_path()
            try:
                copyto = path.join(dspath, tf.name)
                self.storage.path(copyto)
            except (SuspiciousOperation, ValueError):
                copyto = path.join(dspath. path.basename(tf.name))
            try:
                target_replica.url = self.storage.save(copyto, tf)
            except OSError as e:
                raise MigrationProviderError(e.strerror)
            target_replica.verified = False
            target_replica.protocol = ''
            target_replica.save()
    
    def remove_file(self, replica):
        path = self._uri_to_filename(replica.url)
        try:
            self.storage.delete(path)
        except OSError as e:
            raise MigrationProviderError(e.strerror)

    def _uri_to_filename(self, uri):
        # This is crude and possibly fragile, and definitely insecure
        parts = urlparse(uri)
        if not parts.scheme:
            return '%s/%s' % (self.base_path, uri)
        if not uri.startswith(self.base_url):
            raise MigrationProviderError(('The url (%s) does not belong to' \
                                ' the %s destination (url %s)') % \
                                             (uri, self.name, self.base_url))
        return unquote('/%s/%s' % (parts.netloc, parts.path))


class LocalTransfer(BaseLocalTransfer):
    def __init__(self, name, base_url, params):
        BaseLocalTransfer.__init__(self, name, base_url, params)
        parts = urlparse(self.base_url)
        if parts.scheme != 'file':
            raise ValueError('base_url (%s) should be a "file:" url' % base_url)
        self.base_path = parts.path
        self.storage = FileSystemStorage(location=self.base_path)


class CustomTransfer(BaseLocalTransfer):
    def __init__(self, name, base_url, params):
        BaseLocalTransfer.__init__(self, name, base_url, params)
        self.base_path = params['base_path']
        self.storage = FileSystemStorage(location=self.base_path)

    def _uri_to_filename(self, uri):
        # This is crude and possibly fragile, and definitely insecure
        parts = urlparse(uri)
        if not uri.startswith(self.base_url):
            raise MigrationProviderError(('The url (%s) does not belong to' \
                                ' the %s destination (url %s)') % \
                                             (uri, self.name, self.base_url))
        return self.base_path + '/' + uri[len(self.base_url):]

