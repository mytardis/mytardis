from urllib2 import Request, urlopen
from urlparse import urlparse
from django.db import transaction

from tardis.tardis_portal.models import Dataset_File

import logging

logger = logging.getLogger(__name__)

def migrate_datafile_by_id(datafile_id, destination):
    with transaction.commit_on_success():
        datafile = Dataset_File.objects.select_for_update().get(id=datafile_id)
        if not datafile:
            raise RuntimeError('No such datafile (%s)' % (datadile_id))
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
        raise RuntimeError('Cannot migrate a non-local datafile')
        
    target_url = destination.provider.generate_url(datafile)
    if target_url == datafile.url:
        raise RuntimeError('Cannot migrate datafile to its current location')
    
    try:
        destination.provider.transfer_file(datafile, target_url) 
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
    datafile.save()

    
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
        raise RuntimeError('Remote did not return enough metadata for' + \
                           ' file verification')
    except NotSupported:
        pass

    if destination.trust_length :
        try:
            length = destination.provider.get_length(target_url)
            if _check_attribute2(length, datafile.length, 'length'):
                return
        except NotSupported:
            pass
    
    # Fetch back the remote file and verify it locally.
    f = get_privileged_opener().open(target_url)
    md5sum, sha512sum, size = Dataset_File.read_file(f, None, target_url)
    if _check_attribute2(sha512sum, datafile.sha512sum, 'sha512sum') or \
            _check_attribute2(md5sum, datafile.md5sum, 'md5sum'):
        return
    raise RuntimeError('Datafile does not contain enough metadata for' + \
                       ' file verification')

    
def _check_attribute(attributes, value, key):
    if not value:
       return False
    try:
       if attributes[key].lower() != value.lower():
          return True
       raise RuntimeError('Transfer check failed: the %s attribute of the' + \
                          ' remote file does not match' % (key))  
    except KeyError:
       return False;

def _check_attribute2(attribute, value, key):
    if not value or not attribute:
        return False
    if value.lower() == attribute.lower:
        return True
    raise RuntimeError('Transfer check failed: the %s attribute of the' \
                              ' retrieved file does not match' % (key))  

class HeadRequest(Request):
    def get_method(self):
        return 'HEAD'
    
class PutRequest(Request):
    def get_method(self):
        return 'PUT'
    
class DeleteRequest(Request):
    def get_method(self):
        return 'DELETE'
    
class Transfer_Provider:
    def __init__(self, name):
        self.name = name

class Simple_Http_Transfer(Transfer_Provider):
    def __init__(self, name, base_url):
        Transfer_Provider.__init__(self, name)
        self.base_url = base_url
    
    def get_length(self, url):
        self._check_url(url)
        response = urlopen(HeadRequest(url))
        return response.info().getparam('Content-length')
        
    def get_hashes(self, url):
        raise NotImplementedError()
    
    def generate_url(self, datafile):
        url = urlparse(datafile.url)
        if url.scheme == '' or url.scheme == 'file':
            return self.base_url + url.path
        raise RuntimeError("Cannot generate a URL from '%s'" % datafile.url)
    
    def transfer_file(self, datafile, url):
        self._check_url(url)
        with open(datafile.filename) as f:
            content = f.read()
        request = PutRequest(url)
        request.add_header('Content-Length', str(len(content)))
        request.add_header('Content-Type', datafile.mimetype)
        response = urlopen(request, data=content)
        print(response)
    
    def remove_file(self, url):
        raise NotImplementedError()
        
    def _check_url(self, url):
        if url.find(self.base_url) != 0:
            raise RuntimeError(('The url (%s) does not belong to the' + \
                                ' %s destination') % (url, self.name))

class Destination:
    def __init__(self, name):
        descriptor = None
        for d in TRANSFER_DESTINATIONS:
            if d['name'] == name:
                descriptor = d
        if not descriptor:
            raise RuntimeError('Unknown transfer destination %s' % name)
        self.name = descriptor['name']
        self.base_url = descriptor['base_url']
        try:
            self.destination_protocol = descriptor['datafile_protocol']
        except KeyError:
            self.destination_protocol = ''
        tp_class = TRANSFER_PROVIDERS[descriptor['transfer_type']]
        self.provider = tp_class(self.name, self.base_url);
        

TRANSFER_DESTINATIONS = [{'name': 'test', 
                          'transfer_type': 'http',
                          'base_url': 'http://127.0.0.1:4272/data'}]
TRANSFER_PROVIDERS = {'http': Simple_Http_Transfer}
