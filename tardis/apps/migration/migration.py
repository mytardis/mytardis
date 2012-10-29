from urllib2 import Request, urlopen, HTTPError
from urlparse import urlparse
import simplejson, os

from django.db import transaction
from django.conf import settings

from tardis.tardis_portal.models import Dataset_File, generate_file_checksums
from tardis.tardis_portal.fetcher import get_privileged_opener

import logging

logger = logging.getLogger(__name__)

class MigrationError(Exception):
    pass

class MigrationProviderError(MigrationError):
    pass

def migrate_datafile_by_id(datafile_id, destination):
    with transaction.commit_on_success():
        datafile = Dataset_File.objects.select_for_update().get(id=datafile_id)
        if not datafile:
            raise ValueError('No such datafile (%s)' % (datafile_id))
        migrate_datafile(datafile, destination)
                               
def migrate_datafile(datafile, destination):
    """
    Migrate the datafile to a different storage location.  The overall
    effect will be that the datafile will be stored at the new location and 
    removed from the current location, and the datafile metadata will be
    updated to reflect this.
    """

    if not datafile.is_local():
        # If you really want to migrate a non_local datafile, it needs to
        # be localized first.
        raise MigrationError('Cannot migrate a non-local datafile')

    if not datafile.verified or destination.trust_length:
        raise MigrationError('Only verified datafiles can be migrated' \
                                 ' to this destination')
    target_url = destination.provider.generate_url(datafile)
    if target_url == datafile.url:
        raise MigrationError('Cannot migrate a datafile to its' \
                                 ' current location')
    
    try:
        destination.provider.put_file(datafile, target_url) 
    except:
        # FIXME - is the transfer failed because the target url already
        # exists, we should not delete it.
        destination.provider.remove_file(target_url)
        raise
    try:
        check_file_transferred(datafile, destination, target_url)
    except:
        destination.provider.remove_file(target_url)
        raise

    datafile.url = target_url
    datafile.protocol = destination.datafile_protocol
    filename = datafile.filename
    datafile.filename = ''
    datafile.save()
    # FIXME - do this more reliably ...
    os.remove(filename)
    logger.error('Migrated and removed file %s for datafile %s' % \
           (filename, datafile.id))

    
def check_file_transferred(datafile, destination, target_url):
    """
    Check that a datafile has been successfully transfered to a remote
    storage location
    """

    # If the remote is capable, get it to send us the checksums and / or
    # file length for its copy of the file
    try:
        # Fetch the remote's metadata for the file
        m = destination.provider.get_metadata(target_url)
        if _check_attribute(m, datafile.sha512sum, 'sha512sum') or \
               _check_attribute(m, datafile.md5sum, 'md5sum') or \
               (destination.trust_length and \
                 _check_attribute(m, datafile.length, 'length')) :
            return
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
                return
        except NotImplementedError:
            pass
    
    # Fetch back the remote file and verify it locally.
    f = get_privileged_opener().open(target_url)
    md5sum, sha512sum, size, x = generate_file_checksums(f, None)
    if _check_attribute2(sha512sum, datafile.sha512sum, 'sha512sum') or \
            _check_attribute2(md5sum, datafile.md5sum, 'md5sum'):
        return
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
    
class TransferProvider(object):
    def __init__(self, name):
        self.name = name
