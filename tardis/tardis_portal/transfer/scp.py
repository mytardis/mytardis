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
from string import Template
from urlparse import urlparse, urljoin
from contextlib import closing
import os, sys
from paramiko import SSHClient, AutoAddPolicy
from scpclient import SCPError, Write

from .base import TransferError, TransferProvider

import logging
logger = logging.getLogger(__name__)

class ScpTransfer(TransferProvider):
    """A half-hearted attempt at doing transfers using scp.  The root
    problem is that the scp 'protocol' is extremely limited.  You can either
    transfer a single file to an existing directory, or do a full recursive 
    directory copy.  (It would be possible in theory to cause the remote
    to create directories using some tricky stuff and recursive 
    directory copy, but ...)

    Anyhow, this only implements the subset of the TransferProvider API
    needed to do archiving.

    The 'commands' hash provides a 'hook' that allows simple commands to
    be executed via the SSH session on the remote machine, before or after
    the main transfer.
    """
    
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
        self.auto_add = params.get('auto_add_missing_host_key', False)
        self.username = params.get('username', None)
        self.password = params.get('password', None)
        self.key_filename = params.get('key_filename', None)
        self.commands = params.get('commands', {})
        self.ssh = None

    def alive(self):
        ssh = None
        try:
            ssh = self._get_client()
            return True
        except Exception:
            logger.warning('SSH aliveness test failed for provider %s' % 
                           self.name)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('Cause of aliveness failure', 
                             exc_info=sys.exc_info())
            if ssh:
                ssh.get_transport().close()
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
        # Warning: this only works if the dirname part of the archive URL's 
        # path component matches an existing (writable) directory at the
        # remote end.  
        archive_url = self._generate_archive_url(experiment)
        path = urlparse(archive_url).path
        scp = None
        ssh = self._get_client()
        try:
            self._run_command(ssh, 'pre_put_archive', path)
            scp = Write(ssh.get_transport(), os.path.dirname(path))
            scp.send_file(archive_file, remote_filename=os.path.basename(path))
            self._run_command(ssh, 'post_put_archive', path)
        except SCPError as e:
            if scp:
                scp.close()
            raise TransferError(e.message)
        return archive_url

    def _run_command(self, ssh, key, path):
        command_template = self.commands.get(key, None)
        if command_template:
            command = Template(command_template).safe_substitute(
                {'path': path, 
                 'basename': os.path.basename(path),
                 'dirname': os.path.dirname(path)})
            (stdin, stdout, stderr) = ssh.exec_command(command)
            # We need to wait for the status, or else we get a race
            # condition with the command we are going to perform.
            status = stdin.channel.recv_exit_status()
            if status != 0:
                raise TransferError('%s command (%s) failed: status %s' %
                                    (key, command, status))
            # Ignore outputs and input ...
            stdin.close()
            stdout.close()
            stderr.close()
            

    def _get_client(self):
        if self.ssh and not self.ssh.get_transport().is_active():
            return self.ssh
        self.ssh = SSHClient()
        if self.auto_add:
            self.ssh.set_missing_host_key_policy(AutoAddPolicy())
        self.ssh.connect(self.hostname, 
                    port=self.port,
                    username=self.username, 
                    key_filename=self.key_filename, 
                    password=self.password)
        return self.ssh

    def remove_file(self, replica):
        raise NotImplementedError

    def close(self):
        if self.ssh:
            self.ssh.get_transport().close()
