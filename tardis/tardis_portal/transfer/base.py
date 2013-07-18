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
from tardis.tardis_portal.util import generate_file_checksums

class TransferError(Exception):
    pass

class TransferProvider(object):
    def __init__(self, name, base_url, params={}):
        self.name = name
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        self.base_url = base_url
        self.minSize = params.get('min_size', None)
        self.maxSize = params.get('max_size', None)
        self.maxTotalSize = params.get('max_total_size', None)

    def get_file(self, url):
        return self.get_opener(url)()

    def close(self):
        pass

    def check_transfer(self, url, expected, require_checksum=False):
        """
        Check that a file has been successfully transfered.  Try fetching
        the metadata, fetching the length or reading back and checksumming
        the file.  A result of True means we verified at least one checksum,
        and a result of False means we only checked the length.  If a check
        fails, or if there is insufficient info, we raise TransferError.

        The 'url' is the URL of the object to be checked.  The 'expected'
        hash gives the attributes to check against.  If 'require_checksum' 
        is given, it overrides the location's 'trust_length' setting.
        """

        trust_length = not require_checksum and self.trust_length
        
        # If the remote is capable, get it to send us the checksums and / or
        # file length for its copy of the file
        try:
            # Fetch the remote's metadata for the file
            m = self.get_metadata(url)
            self._check_attr(m, expected, 'length')
            if (self._check_attr(m, expected, 'sha512sum') or \
                    self._check_attr(m, expected, 'md5sum')):
                return True
            if trust_length and self._check_attr(m, expected, 'length') :
                return False
            raise TransferError('Not enough metadata for verification')
        except NotImplementedError:
            pass

        if trust_length :
            try:
                length = self.get_length(replica.url)
                if self._check_attr2(length, expected, 'length'):
                    return False
            except NotImplementedError:
                pass
    
        # Fetch back the remote file and verify it locally.
        f = self.get_file(url)
        md5sum, sha512sum, size, _ = generate_file_checksums(f, None)
        self._check_attr2(str(size), expected, 'length')
        if self._check_attr2(sha512sum, expected, 'sha512sum') or \
                self._check_attr2(md5sum, expected, 'md5sum'):
            return True
        raise TransferError('Not enough metadata for file verification')
    

    def _check_attr(self, attributes, expected, key):
        return self._check_attr2(attributes.get(key, None), expected, key)
        
    def _check_attr2(self, attribute, expected, key):
        """Check that the 'attribute' value matches the corresponding
        value in 'expected'.  If there is a mismatch throw TransferError.
        Otherwise 'True' means that the match succeeded, 'False' means 
        no information.
        """

        value = expected.get(key, None)
        if not value or not attribute:
            return False
        if value.lower() == attribute.lower():
            return True
        logger.debug('incorrect %s: expected %s, got %s', key, value, attribute)
        raise TransferError('Transfer check failed: the %s of the target '
                            ' file does not match' % key)
    
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

