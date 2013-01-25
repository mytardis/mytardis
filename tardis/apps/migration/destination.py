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
from tardis.tardis_portal.models import Location

class Destination:

    destinations = {}
    
    @classmethod
    def clear_destinations_cache(cls):
        cls.destinations = {}

    @classmethod
    def get_destination(cls, name):
        try:
            return cls.destinations[name]
        except KeyError:
            dest = cls._load_destination(name)
            if dest:
                cls.destinations[name] = dest
                return dest
            raise ValueError('Unknown destination %s' % name)

    @classmethod
    def _load_destination(cls, name):
        loc = Location.get_location(name);
        if not loc:
            return None
        dest = Destination()
        dest.loc_id = loc.id
        dest.name = loc.name
        dest.base_url = loc.url
        dest.trust_length = loc.trust_length
        dest.metadata_supported = loc.metadata_supported
        if loc.auth_user:
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(loc.auth_realm, dest.base_url, 
                                      loc.auth_user, loc.auth_password)
            if loc.auth_scheme == 'basic':
                handler = urllib2.HTTPBasicAuthHandler(password_mgr)
            elif loc.auth_scheme == 'digest':
                handler = urllib2.HTTPDigestAuthHandler(password_mgr)
            else:
                raise ValueError('Unknown auth type "%s"' % loc.auth_scheme)
            dest.opener = urllib2.build_opener(handler)
        else:
            dest.opener = urllib2.build_opener()

        # FIXME - is there a better way to do this?
        exec 'import tardis\n' + \
            'dest.provider = ' + \
            settings.MIGRATION_PROVIDERS[loc.migration_provider] + \
                '(loc.name, loc.url, dest.opener, ' + \
                'metadata_supported=loc.metadata_supported)'

        return dest

