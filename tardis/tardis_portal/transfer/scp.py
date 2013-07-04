#
# Copyright (c) 2013, Centre for Microscopy and Microanalysis
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

from urllib import quote
from urlparse import urlparse, urljoin
import os
from paramiko import SSHClient
from scpclient import SCPError, Write

from .base import TransferError, TransferProvider

import logging
logger = logging.getLogger(__name__)

class ScpTransfer(TransferProvider):
    
    def __init__(self, name, base_url, params):
        TransferProvider.__init__(self, name, base_url)
        parts = urlparse(base_url)
        if parts.scheme != 'scp':
            raise ValueError('scp: url required for transfer provider (%s)' %
                             name)
        if parts.username or parts.password:
            raise ValueError('url for transfer provider (%s) cannot use' 
                             ' a username or password' % name)
        if parts.path.find('#') != -1 or parts.path.find('?') != -1 or \
                parts.path.find(';') != -1:
            logger.warning('The base url for transfer provider (%s) appears'
                           ' to contain an http-style path param, query or'
                           ' fragment marker.  It will be treated as a plain'
                           ' pathname character')
        if not parts.hostname or not parts.path:
            raise ValueError('url for transfer provider (%s) requires a '
                             'non-empty hostname and path' % name)
        self.hostname = parts.hostname
        self.port = parts.port if parts.port else 22
        
        self.metadata_supported = False
        self.trust_length = params.get('trust_length', 'False') == 'True'
        self.username = params.get('username', None)
        self.password = params.get('password', None)
        self.key_filename = params.get('key_filename', None)

    def alive(self):
        try:
            with closing(self._get_client()) as scp:
                return True
        except Exception:
            logger.warning('SSH aliveness test failed for provider %s' % 
                           self.name)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('Cause of aliveness failure', sys.exc_info())
            return False

    def get_length(self, replica):
        raise NotImplementedError
        
    def get_metadata(self, replica):
        raise NotImplementedError
    
    def get_opener(self, replica):
        raise NotImplementedError

    def generate_url(self, replica):
        raise NotImplementedError

    def put_file(self, source_replica, target_replica):
        raise NotImplementedError

    def put_archive(self, archive_file, experiment):
        archive_url = self._generate_archive_url(experiment)
        try:
            parts = urlparse.parse(archive_url)
            path = parts.path
            scp = Write(self._get_client().get_transport(), "/")
            scp.send_file(archive_file, path)
        except SCPError as e:
            raise TransferError(e.msg)
        finally:
            scp.close()
            
        return archive_url

    def _get_client(self):
        ssh = SSHClient()
        ssh.connect(self.hostname, 
                    port=self.port,
                    username=self.username, 
                    key_filename=self.key_filename, 
                    password=self.password)
        return ssh

    def remove_file(self, replica):
        raise NotImplementedError

