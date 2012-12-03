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

import urllib2

from django.conf import settings

from tardis.apps.migration import MigrationError


class Destination:

    destinations = None
    
    @classmethod
    def clear_destinations_cache(cls):
        cls.destinations = None

    @classmethod
    def get_destination(cls, name):
        try:
            return cls._get_destinations()[name]
        except KeyError:
            raise ValueError('Unknown destination %s' % name)

    @classmethod
    def _get_destinations(cls):
        if cls.destinations == None:
            if len(settings.MIGRATION_DESTINATIONS) == 0:
                raise MigrationError("No destinations have been configured")
            cls.destinations = {}
            for d in settings.MIGRATION_DESTINATIONS:
                cls.destinations[d['name']] = Destination(d)
        return cls.destinations

    @classmethod
    def identify_destination(cls, url):
        for d in cls._get_destinations().values():
            if d.provider.url_matches(url):
                return d
        return None

    def __init__(self, descriptor):
        self.name = descriptor['name']
        self.base_url = descriptor['base_url']
        self.trust_length = descriptor.get('trust_length', False)
        self.datafile_protocol = descriptor.get('datafile_protocol', '')
        self.metadata_supported = descriptor.get('metadata_supported', False)
        
        user = descriptor.get('user')
        if user:
            password = descriptor.get('password', '')
            realm = descriptor.get('realm', None)
            auth = descriptor.get('auth', 'digest')
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(realm, self.base_url, user, password)
            if auth == 'basic':
                handler = urllib2.HTTPBasicAuthHandler(password_mgr)
            elif auth == 'digest':
                handler = urllib2.HTTPDigestAuthHandler(password_mgr)
            else:
                raise ValueError('Unknown auth type "%s"' % auth)
            self.opener = urllib2.build_opener(handler)
        else:
            self.opener = urllib2.build_opener()

        # FIXME - is there a better way to do this?
        exec 'import tardis\n' + \
            'self.provider = ' + \
            settings.MIGRATION_PROVIDERS[descriptor['transfer_type']] + \
                '(self.name, self.base_url, self.opener, ' + \
                'metadata_supported=self.metadata_supported)'

