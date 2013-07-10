#
# Copyright (c) 2012-2013, Centre for Microscopy and Microanalysis
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
from urlparse import urljoin

class TransferError(Exception):
    pass

class TransferProvider(object):
    def __init__(self, name, base_url):
        self.name = name
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        self.base_url = base_url

    def get_file(self, replica):
        return self.get_opener(replica)()

    def close(self):
        pass

    def generate_url(self, replica):
        return replica.generate_default_url()

    def _generate_archive_url(self, experiment):
        path = '%s-archive.tar.gz' % experiment.id
        return urljoin(self.base_url, quote(path))

    def _check_url(self, url):
        if not url.startswith(self.base_url):
            raise TransferError(
                'url %s does not belong to the %s destination (url %s)' % \
                    (url, self.name, self.base_url))

    def _isTrue(self, params, key, default):
        value = params.get(key, None)
        if value == None:
            return default
        if isinstance(value, basestring):
            return value.upper() == 'TRUE'
        else:
            return value

