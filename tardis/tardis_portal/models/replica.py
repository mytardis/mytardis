from magic import Magic
from urllib2 import build_opener
from urlparse import urlparse
import sys

from django.conf import settings
from django.db import models
from django.core.urlresolvers import reverse
from django.core.files.storage import default_storage
from django.utils import _os

from tardis.tardis_portal.util import generate_file_checksums
from tardis.tardis_portal.fetcher import get_privileged_opener


from .location import Location

import logging
logger = logging.getLogger(__name__)

class Replica(models.Model):
    """Class to store meta-data about a physical file replica

    :attribute datafile: the foreign key to the
       :class:`tardis.tardis_portal.models.Dataset_File` the replica belongs to.
    :attribute url: the url for the replica.  If the file is online, this
       url should be resolveable to a file that contains the data for the
       Dataset_File.  For offline replicas, the url may represent an element
       within an archive.  The archive is not necessarily directly fetchable.
    :attribute protocol: TBD
    :attribute verified: the content of the replica has been verified against
       the size and checksums recorded in the Dataset_File.
    :attribute location: the foreign key for the Location that holds the
       Replica.  In the case of a Replica that is a member of an archive, the
       Location denoted the container for the archive not the archive itself.
    :attribute stay_remote: is used (temporarily) to indicate to the ingestion
       task that a file should not be copied into the mytardis

    """

    datafile = models.ForeignKey('Dataset_File')
    url = models.CharField(max_length=400)
    protocol = models.CharField(blank=True, max_length=10)
    verified = models.BooleanField(default=False)
    stay_remote = models.BooleanField(default=False)
    location = models.ForeignKey(Location)

    class Meta:
        app_label = 'tardis_portal'

    def is_local(self):
        """Return True if this replica is accessible from the file system.
        """

        try:
            if self.protocol in (t[0] for t in settings.DOWNLOAD_PROVIDERS):
                return False
        except AttributeError:
            pass
        return urlparse(self.url).scheme == ''
    
    def get_actual_url(self):
        """Return a URL for this replica that should be resolvable within
        this MyTardis application platform.  This should be a well-formed
        URL with scheme http, https, ftp or file.
        """

        if self.is_local():
            # Local file
            return 'file://'+self.get_absolute_filepath()
        # Remote files are also easy
        url = urlparse(self.url)
        if url.scheme in ('http', 'https', 'ftp', 'file'):
            return self.url
        return None
    
    def get_file_getter(self, requireVerified=True):
        """Return a function that will return a File-like handle for the 
        replica's data.  The returned function uses a cached URL for the 
        file to avoid depending on the current database transaction.
        """
        
        if requireVerified and not self.verified:
            raise ValueError("Replica %s not verified" % self.id)
        if self.is_local():
            theUrl = self.url
            def getter():
                return default_storage.open(theUrl)
            return getter
        else:
            theUrl = self.get_actual_url()
            def getter():
                return get_privileged_opener().open(theUrl)
            return getter

    def get_file(self, requireVerified=True):
        return self.get_file_getter(requireVerified=requireVerified)()

    def get_download_url(self):
        def get_download_view():
            # Handle external protocols
            try:
                for module in settings.DOWNLOAD_PROVIDERS:
                    if module[0] == self.protocol:
                        return '%s.download_datafile' % module[1]
            except AttributeError:
                pass
            # Fallback to internal
            url = urlparse(self.url)
            # These are internally known protocols
            if url.scheme in ('', 'http', 'https', 'ftp', 'file'):
                return 'tardis.tardis_portal.download.download_datafile'
            return None

        try:
            return reverse(get_download_view(),
                           kwargs={'datafile_id': self.id})
        except:
            return ''

    def get_absolute_filepath(self):
        url = urlparse(self.url)
        if url.scheme == '':
            try:
                # FILE_STORE_PATH must be set
                return _os.safe_join(settings.FILE_STORE_PATH, url.path)
            except AttributeError:
                return ''
        if url.scheme == 'file':
            return url.path
        # ok, it doesn't look like the file is stored locally
        else:
            return ''

    def verify(self, tempfile=None, allowEmptyChecksums=False):
        '''
        Verifies this replica's data matches the Datafile checksums. 
        It must have at least one checksum hash to verify unless 
        "allowEmptyChecksums" is True.

        If passed a file handle, it will write the file to it instead of
        discarding data as it's read.
        '''

        from .datafile import Dataset_File
        df = Dataset_File.objects.get(pk=self.datafile.pk)
        if not (allowEmptyChecksums or df.sha512sum or df.md5sum):
            logger.error("Datafile for %s has no checksums" % self.url)
            return False

        sourcefile = self.get_file(requireVerified=False)
        if not sourcefile:
            logger.error("%s content not accessible" % self.url)
            return False
        logger.info("Downloading %s for verification" % self.url)
        md5sum, sha512sum, size, mimetype_buffer = \
            generate_file_checksums(sourcefile, tempfile)

        if not (df.size and size == int(df.size)):
            if (df.sha512sum or df.md5sum) and not df.size: 
                # If the size is missing but we have a checksum to check
                # the missing size is harmless ... we will fill it in below.
                logger.warn("%s size is missing" % (self.url))
            else:
                logger.error("%s failed size check: %d != %s" %
                            (df.url, size, df.size))
                return False

        if df.sha512sum and sha512sum.lower() != df.sha512sum.lower():
            logger.error("%s failed SHA-512 sum check: %s != %s" %
                         (self.url, sha512sum, df.sha512sum))
            return False

        if df.md5sum and md5sum.lower() != df.md5sum.lower():
            logger.error("%s failed MD5 sum check: %s != %s" %
                         (self.url, md5sum, df.md5sum))
            return False

        if df.mimetype:
            mimetype = df.mimetype
        elif len(mimetype_buffer) > 0:
            mimetype = Magic(mime=True).from_buffer(mimetype_buffer)
        else:
            mimetype = ''
        if not (df.size and df.md5sum and df.sha512sum and df.mimetype):
            df.md5sum = md5sum.lower()
            df.sha512sum = sha512sum.lower()
            df.size = str(size)
            df.mimetype = mimetype
            df.save()
        self.verified = True
        self.save()

        logger.info("Saved %s for datafile #%d " % (self.url, self.id) +
                    "after successful verification")
        return True
    
    def deleteCompletely(self):
        import os
        filename = self.get_absolute_filepath()
        os.remove(filename)
        self.delete()

                    

