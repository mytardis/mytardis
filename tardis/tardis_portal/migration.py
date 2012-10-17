import urllib2
import logging

logger = logging.getLogger(__name__)

def migrate_datafile(datafile, destination):
    target_url = destination.transfer_provider.generate_url(datafile)
    if target_url == datafile.url:
        return
    transfered = destination.transfer_provider.transfer_file(datafile, target_url)
    if check_file_transferred(datafile, destination, target_url):
        datafile.url = target_url
        datafile.save()
        return True
    else:
        if transferred:
            destination.transfer_provider.cleanup(target_url)
        return False
    
def check_file_transferred(datafile, destination, target_url):
    try:
        (sha512, md5) = destination.transfer_provider.get_hashes(target_url)
        if sha512 and datafile.sha512sum:
            return sha512.lower() == datafile.sha512sum.lower()
        if md5 and datafile.md5sum:
            return md5.lower() == datafile.md5sum.lower()
    except NotSupported:
        pass
    try:
        length = destination.transfer_provider.get_length(target_url)
        return length == datafile.length
    except:
        return False
    
class HeadRequest(urllib2.Request):
    def get_method(self):
        return 'HEAD'
    
class PutRequest(urllib2.Request):
    def get_method(self):
        return 'PUT'
    
class DeleteRequest(urllib2.Request):
    def get_method(self):
        return 'DELETE'
    
class Simple_Http_Transfer:
    def __init__(self, **kwargs):
        self.base_url = kwargs['base_url']
        self.name = kwargs['name']
    
    def get_length(self, url):
        self._check_url(url)
        try:
            response = urllib2.urlopen(HeadRequest(url))
            return int(response.info().getparam('Content-length'))
        except HTTPError as e:
            logger.debug('Http HEAD request for %s failed: %d' % (url, e.code))
            return -1
        except URLError as e:
            logger.debug('Cannot contact %s: %s' % (url, e.reason[1]))
            return -1
        
    def get_hashes(self, url):
        raise NotImplementedError()
    
    def generate_url(self, datafile):
        raise NotImplementedError()
    
    def transfer_file(self, datafile, url):
        raise NotImplementedError()
    
    def cleanup(self, url):
        raise NotImplementedError()
        
    def _check_url(self, url):
        if not url.startsWith(base_url):
            raise RuntimeError('The url (%s) does not belong to the %s transfer provider' % (url, self.name))

TRANSFER_DESTINATIONS = ({name: 'test', type: 'http', base_url : 'http://localhost:/data'})
TRANSFER_PROVIDERS = [('http', 'tardis.tardis_portal.migration.Simple_Http_Transfer')]