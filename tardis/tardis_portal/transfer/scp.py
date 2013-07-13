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
from urlparse import urlparse, urljoin, uses_netloc, uses_relative
from contextlib import closing
from subprocess import Popen, STDOUT, PIPE
from tempfile import NamedTemporaryFile
import os, sys, subprocess

from .base import TransferError, TransferProvider

import logging
logger = logging.getLogger(__name__)

# Monkey-patch the urlparser code to grok "scp:" URLs.
uses_netloc.append('scp')
uses_relative.append('scp')


class ScpTransfer(TransferProvider):
    """So far, this only implements the subset of the TransferProvider API
    needed to do archiving.

    The 'commands' hash provides a 'hook' that allows simple commands to
    be executed via the SSH session on the remote machine, before or after
    the main transfer.  This also allows to to override certain commands
    that are used by default.
    """
    
    def __init__(self, name, base_url, params):
        TransferProvider.__init__(self, name, base_url, params)
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
        
        self.username = params.get('username', None)
        if not self.username:
            raise ValueError('No username parameter found')
             
        self.metadata_supported = True
        self.trust_length = self._isTrue(params, 'trust_length', False)
        self.commands = {
            'echo': '${ssh} echo hi',
            'mkdirs': '${ssh} mkdir -p "${path}"',
            'length': '${ssh} stat --format="%s" "${path}"',
            'remove': '${ssh} rm "${path}"',
            'scp_from': 'scp ${scp_opts} ${username}@${hostname}:"${remote}" "${local}"',
            'scp_to': 'scp ${scp_opts} "${local}" ${username}@${hostname}:"${remote}"',
            'ssh': 'ssh -o PasswordAuthentication=no ${ssh_opts} ${username}@${hostname}'}
        self.commands.update(params.get('commands', {}))
        # deal with the 'flattened' command params from a Location
        for (key, value) in params.items():
            if key.startswith('command_'):
                self.commands[key[len('command_'):]] = value 
        self.base_url_path = urlparse(self.base_url).path

        self.key_filename = params.get('key_filename', None)
        self.hostname = parts.hostname
        self.port = parts.port if parts.port else 22

    def _get_scp_opts(self):
        opts = ''
        if self.key_filename:
            opts += ' -i %s' % self.key_filename
        if self.port != 22:
            opts += ' -P %s' % self.port
        return opts

    def _get_ssh_command(self):
        opts = ''
        if self.key_filename:
            opts += ' -i %s' % self.key_filename
        if self.port != 22:
            opts += ' -p %s' % self.port
        
        template = self.commands.get('ssh')
        return Template(template).safe_substitute(
                username=self.username,
                hostname=self.hostname,
                ssh_opts=opts)

    def alive(self):
        try:
            output = self.run_command('echo', {})
            if output == 'hi\n':
                return True
            else:
                logger.debug("SSH remote echo output is incorrect")
                return False
        except Exception as e:
            logger.warning('SSH aliveness test failed for provider %s' %
                           self.name)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('Cause of aliveness failure',
                             exc_info=sys.exc_info())
            return False

    def get_length(self, url):
        (path, _, _) = self._analyse_url(url)
        return int(self.run_command('length', {'path': path}).strip())
    
    def get_metadata(self, replica):
        raise NotImplementedError
    
    def get_opener(self, url):
        (path, _, _) = self._analyse_url(url)
        tmpFile = NamedTemporaryFile(mode='rb', prefix='mytardis_scp_', 
                                     delete=False)
        name = tmpFile.name
        self.run_command('scp_from', 
                         {'local': name, 'remote': path})

        def opener():
            return _TemporaryFileWrapper(name)
        return opener

    def put_replica(self, source_replica, target_replica):
        source_path = source_replica.get_absolute_filepath()
        # The 'scp' command copies to and from named files, so a
        # remote replica has to be fetched to a local temp file ...
        if source_path:
            return self.put_file(source_path, target_replica.url, 'replica')
        else:
            with closing(source_replica.get_file()) as f:
                with closing(NamedTemporaryFile(
                        mode='w+b', prefix='mytardis_scp_')) as t:
                    shutil.copyFileObj(f, t)
                    t.flush()
                    return self.put_file(t.name, target_replica.url, 'replica')

    def put_archive(self, archive_filename, archive_url):
        return self.put_file(archive_filename, archive_url, 'archive')

    def put_file(self, source_filename, url, kind='file', 
                 content_type=None, content_length=None):
        (path, dirname, filename) = self._analyse_url(url)
        self.run_hook(['pre_put_%s' % kind, 'pre_put_file'], 
                      {'path': path, 'dirname': dirname, 'filename': filename})
        if self.base_url_path != dirname:
            self.run_command('mkdirs', {'path': dirname})
        self.run_command('scp_to', 
                         {'local': source_filename, 'remote': path})
        self.run_hook(['pre_put_%s' % kind, 'pre_put_file'], 
                      {'path': path, 'dirname': dirname, 'filename': filename})
        return url

    def remove_file(self, url):
        (path, _, _) = self._analyse_url(url)
        self.run_command('remove', {'path': path})

    def close(self):
        pass

    def _analyse_url(self, url):
        self._check_url(url)
        path = urlparse(url).path
        dirname = os.path.dirname(path)
        filename = os.path.basename(path)
        return (path, dirname, filename)

    def run_hook(self, keys, params):
        for key in keys:
            template = self.commands.get(key, None)
            if template:
                return self._do_run_command(template, params)
        return None

    def run_command(self, key, params):
        template = self.commands.get(key, None)
        if not template:
            raise TransferError('No command found for %s' % key)
        return self._do_run_command(template, params)

    def _do_run_command(self, template, params):      
        params['ssh'] = self._get_ssh_command()
        params['username'] = self.username 
        params['hostname'] = self.hostname
        params['scp_opts'] = self._get_scp_opts()
        command = Template(template).safe_substitute(params)
        logger.debug(command)

        process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
        output, unused_err = process.communicate()
        rc = process.poll()
        if rc:
            logger.debug('error output: %s\n' % output)
            raise TransferError('command %s failed: rc %s' % (command, rc))
        return output

class _TemporaryFileWrapper:
    # This is a cut-down / hacked about version of the same named
    # class in tempfile.  Main differences are 1) delete is hard-wired
    # 2) we open our own file object, 3) there is no __del__ because
    # it causes premature closing, and 4) stripped out the Windows.NT stuff.
    def __init__(self, name):
        self.name = name
        self.file = open(name, 'rb')
        self.close_called = False

    def __getattr__(self, name):
        file = self.__dict__['file']
        a = getattr(file, name)
        if not issubclass(type(a), type(0)):
            setattr(self, name, a)
        return a

    def __enter__(self):
        self.file.__enter__()
        return self

    def close(self):
        if not self.close_called:
            self.close_called = True
            self.file.close()
            if self.delete:
                os.unlink(self.name)
                    
    def __exit__(self, exc, value, tb):
        result = self.file.__exit__(exc, value, tb)
        self.close()
        return result
