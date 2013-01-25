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


from urllib2 import Request, urlopen, HTTPError
from urlparse import urlparse
import os

from django.conf import settings
from django.db import transaction

from tardis.tardis_portal.fetcher import get_privileged_opener
from tardis.tardis_portal.staging import stage_replica
from tardis.tardis_portal.util import generate_file_checksums

from tardis.apps.migration import Destination, MigrationError

import logging

logger = logging.getLogger(__name__)


def migrate_datafile_by_id(replica_id, destination,
                          noRemove=False, noUpdate=False):
    raise Exception('tbd')

def migrate_replica_by_id(replica_id, destination,
                          noRemove=False, noUpdate=False):
    # (Deferred import to avoid prematurely triggering DB init)
    from tardis.tardis_portal.models import Replica
    
    replica = Replica.objects.get(id=replica_id)
    if not datafile:
        raise ValueError('No such replica (%s)' % (replica_id))
    return migrate_datafile(datafile, destination, 
                            noRemove=noRemove, noUpdate=noUpdate)
                               
def migrate_datafile(replica, destination, noRemove=False, noUpdate=False):
    raise Exception('tbd')


def migrate_replica(replica, destination, noRemove=False, noUpdate=False):
    """
    Migrate the replica to a different storage location.  The overall
    effect will be that the datafile will be stored at the new location and 
    removed from the current location, and the datafile metadata will be
    updated to reflect this.
    """

    from tardis.tardis_portal.models import Replica, Location

    with transaction.commit_on_success():
        replica = Replica.objects.select_for_update().get(pk=replica.pk)
        location = Location.objects.get(pk=destination.loc_id)
        
        if not replica.verified or destination.trust_length:
            raise MigrationError('Only verified datafiles can be migrated' \
                                     ' to this destination')
        
        if Replica.objects.filter(datafile=replica.datafile,
                                  location__id=destination.loc_id):
            raise MigrationError('A replica already exists at the destination')
        
        target_url = destination.provider.generate_url(replica)
        if target_url == replica.url:
            # We should get here ...
            raise MigrationError('Cannot migrate a replica to its' \
                                     ' current location')
        
        destination.provider.put_file(replica, target_url) 
        verified = False
        try:
            verified = check_file_transferred(replica, destination, target_url)
        except:
            # FIXME - should we always do this?
            destination.provider.remove_file(target_url)
            raise

        newreplica = Replica()
        newreplica.datafile = replica.datafile
        newreplica.url = target_url
        newreplica.protocol = ''
        newreplica.verified = verified
        newreplica.location = location
        newreplica.stay_remote = location != Location.get_default_location()
        newreplica.save()
        
        if noUpdate:
            return True
        
        filename = replica.get_absolute_filepath()
        logger.info('Migrated file %s for replica %s' %
                    (filename, replica.id))
    
        # FIXME - do this more reliably ...
        if not noRemove:
            replica.delete()
            os.remove(filename)
            logger.info('Removed local file %s for replica %s' %
                        (filename, replica.id))
        return True

def restore_datafile_by_id(replica_id, noRemove=False):
    raise Exception('tbd')

def restore_replica_by_id(replica_id, noRemove=False):
    # (Deferred import to avoid prematurely triggering DB init)
    from tardis.tardis_portal.models import Replica

    replica = Replica.objects.select_for_update().get(id=replica_id)
    if not replica:
        raise ValueError('No such replica (%s)' % (replica_id))
    return restore_replica(replica, noRemove=noRemove)
                               
def restore_datafile(replica, noRemove=False):
    raise Exception('tbd')

def restore_replica(replica, noRemove=False):
    """
    Restore a file that has been migrated
    """
    
    # (Deferred imports to avoid prematurely triggering DB init)
    from tardis.tardis_portal.models import Replica
    from django.db import transaction
    with transaction.commit_on_success():
        rep = Replica.objects.select_for_update().get(id=replica.id)
        if rep.is_local():
            return False
        destination = Destination.identify_destination(rep.url)
        if not destination:
            raise MigrationError('Cannot identify the migration destination' \
                                     ' holding %s' % rep.url)
        if not rep.verified or destination.trust_length:
            raise MigrationError('Only verified replicas can be restored' \
                                 ' from destination %s' % destination.name)
        rep.verified = False
        url = rep.url
        if not stage_replica(rep):
            raise MigrationError('Restoration failed')
        logger.info('Restored file %s for replica %s' %
                    (rep.get_absolute_filepath(), rep.id))
        if not noRemove:
            destination.provider.remove_file(url)
            logger.info('Removed remote file %s for replica %s' % (url, rep.id))
        return True
    
def check_file_transferred(replica, destination, target_url):
    """
    Check that a replica has been successfully transfered to a remote
    storage location
    """

    from tardis.tardis_portal.models import Dataset_File
    datafile = Dataset_File.objects.get(pk=replica.datafile.id)
    print "datafile %s - %s / %s / %s\n" % (datafile.id, datafile.size,
                                            datafile.md5sum, datafile.sha512sum)

    # If the remote is capable, get it to send us the checksums and / or
    # file length for its copy of the file
    try:
        # Fetch the remote's metadata for the file
        m = destination.provider.get_metadata(target_url)
        if _check_attribute(m, datafile.sha512sum, 'sha512sum') or \
               _check_attribute(m, datafile.md5sum, 'md5sum'):
            return True
        if destination.trust_length and \
                 _check_attribute(m, datafile.length, 'length') :
            return False
        raise MigrationError('Not enough metadata for verification')
    except NotImplementedError:
        pass
    except HTTPError as e:
        # Bad request means that the remote didn't recognize the query
        if e.code != 400:
            raise

    if destination.trust_length :
        try:
            length = destination.provider.get_length(target_url)
            if _check_attribute2(length, datafile.length, 'length'):
                return False
        except NotImplementedError:
            pass
    
    # Fetch back the remote file and verify it locally.
    f = get_privileged_opener().open(target_url)
    md5sum, sha512sum, size, x = generate_file_checksums(f, None)
    if _check_attribute2(sha512sum, datafile.sha512sum, 'sha512sum') or \
            _check_attribute2(md5sum, datafile.md5sum, 'md5sum'):
        return True
    raise MigrationError('Not enough metadata for file verification')
    
def _check_attribute(attributes, value, key):
    if not value:
       return False
    try:
       if attributes[key].lower() == value.lower():
          return True
       raise MigrationError('Transfer check failed: the %s attribute of the' \
                                ' remote file does not match' % (key))  
    except KeyError:
       return False;

def _check_attribute2(attribute, value, key):
    if not value or not attribute:
        return False
    if value.lower() == attribute.lower():
        return True
    raise MigrationError('Transfer check failed: the %s attribute of the' \
                           ' retrieved file does not match' % (key))


    
