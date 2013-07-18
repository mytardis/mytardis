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


from urllib2 import Request, urlopen, HTTPError
from urlparse import urlparse
import os

from django.conf import settings
from django.db import transaction

from tardis.tardis_portal.fetcher import get_privileged_opener
from tardis.tardis_portal.staging import stage_replica
from tardis.tardis_portal.util import generate_file_checksums
from tardis.tardis_portal.transfer import TransferError

from tardis.apps.migration import MigrationError

import logging

logger = logging.getLogger(__name__)


def migrate_replica_by_id(replica_id, location,
                          noRemove=False, mirror=False):
    # (Deferred import to avoid prematurely triggering DB init)
    from tardis.tardis_portal.models import Replica
    
    replica = Replica.objects.get(id=replica_id)
    if not replica:
        raise ValueError('No such replica (%s)' % (replica_id))
    return migrate_replica(replica, location, 
                            noRemove=noRemove, mirror=mirror)
                               
def migrate_replica(replica, location, noRemove=False, mirror=False):
    """
    Migrate the replica to a different storage location.  The overall
    effect will be that the datafile will be stored at the new location and 
    removed from the current location, and the datafile metadata will be
    updated to reflect this.
    """

    from tardis.tardis_portal.models import Replica, Location

    with transaction.commit_on_success():
        replica = Replica.objects.select_for_update().get(pk=replica.pk)
        source = Location.get_location(replica.location.name)
        
        if not replica.verified or location.provider.trust_length:
            raise MigrationError('Only verified datafiles can be migrated' \
                                     ' to this destination')
        
        filename = replica.get_absolute_filepath()
        try:
            newreplica = Replica.objects.get(datafile=replica.datafile,
                                             location=location)
            created_replica = False
            # We've most likely mirrored this file previously.  But if
            # we are about to delete the source Replica, we need to check
            # that the target Replica still verifies.
            if not mirror and not check_file_transferred(newreplica, location):
                raise MigrationError('Previously mirrored / migrated Replica' \
                                         ' no longer verifies locally!')
        except Replica.DoesNotExist:
            newreplica = Replica()
            newreplica.location = location
            newreplica.datafile = replica.datafile
            newreplica.protocol = ''
            newreplica.stay_remote = location != Location.get_default_location()
            newreplica.verified = False

            url = newreplica.generate_default_url()
            
            if newreplica.url == url:
                # We should get here ...
                raise MigrationError('Cannot migrate a replica to its' \
                                         ' current location')
            newreplica.url = url
            newreplica.url = location.provider.put_replica(replica, newreplica) 
            verified = False
            try:
                verified = check_file_transferred(newreplica, location)
            except:
                # FIXME - should we always do this?
                location.provider.remove_file(newreplica.url)
                raise
            
            newreplica.verified = verified
            newreplica.save()
            logger.info('Transferred file %s for replica %s' %
                        (filename, replica.id))
            created_replica = True
        
        if mirror:
            return created_replica

        # FIXME - do this more reliably ...
        replica.delete()
        if not noRemove:
            source.provider.remove_file(replica.url)
            logger.info('Removed local file %s for replica %s' %
                        (filename, replica.id))
        return True

def check_file_transferred(replica, location):
    """
    Check that a replica has been successfully transfered to a remote
    storage location
    """

    from tardis.tardis_portal.models import Dataset_File
    datafile = Dataset_File.objects.get(pk=replica.datafile.id)
    try:
        return location.provider.check_transfer(
            replica.url,
            {'length': datafile.size,
             'md5sum': datafile.md5sum,
             'sha512sum': datafile.sha512sum})
    except TransferError as e:
        raise MigrationError(e.args[0])
    
