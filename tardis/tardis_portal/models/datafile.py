from os import path

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import pre_save

from .dataset import Dataset

import logging
logger = logging.getLogger(__name__)

class Dataset_File(models.Model):
    """Class to store meta-data about a physical file

    :attribute dataset: the foreign key to the
       :class:`tardis.tardis_portal.models.Dataset` the file belongs to.
    :attribute filename: the name of the file, excluding the path.
    :attribute url: the url that the datafile is located at
    :attribute size: the size of the file.
    :attribute protocol: the protocol used to access the file.
    :attribute created_time: time the file was added to tardis
    :attribute modification_time: last modification time of the file
    :attribute mimetype: for example 'application/pdf'
    :attribute md5sum: digest of length 32, containing only hexadecimal digits

    The `protocol` field is only used for rendering the download link, this
    done by insterting the protocol into the url generated to the download
    location. If the `protocol` field is blank then the `file` protocol will
    be used.
    """

    dataset = models.ForeignKey(Dataset)
    filename = models.CharField(max_length=400)
    url = models.CharField(max_length=400)
    size = models.CharField(blank=True, max_length=400)
    protocol = models.CharField(blank=True, max_length=10)
    created_time = models.DateTimeField(null=True, blank=True)
    modification_time = models.DateTimeField(null=True, blank=True)
    mimetype = models.CharField(blank=True, max_length=80)
    md5sum = models.CharField(blank=True, max_length=32)

    class Meta:
        app_label = 'tardis_portal'

    def getParameterSets(self, schemaType=None):
        """Return datafile parametersets associated with this experiment.

        """
        from tardis.tardis_portal.models.parameters import Schema
        if schemaType == Schema.DATAFILE or schemaType is None:
            return self.datafileparameterset_set.filter(
                schema__type=Schema.DATAFILE)
        else:
            raise Schema.UnsupportedType

    def __unicode__(self):
        return self.filename

    def get_mimetype(self):
        if self.mimetype:
            return self.mimetype
        else:
            suffix = self.filename.split('.')[-1]
            try:
                import mimetypes
                return mimetypes.types_map['.%s' % suffix.lower()]
            except KeyError:
                return 'application/octet-stream'

    def get_view_url(self):
        from tardis.tardis_portal.download \
            import IMAGEMAGICK_AVAILABLE, MIMETYPES_TO_VIEW_AS_PNG
        import re
        viewable_mimetype_patterns = ['image/.*', 'text/.*']
        if not any(re.match(p, self.get_mimetype())
                   for p in viewable_mimetype_patterns):
            return None
        # We should avoid listing files that require conversion
        if (not IMAGEMAGICK_AVAILABLE and
            self.get_mimetype() in MIMETYPES_TO_VIEW_AS_PNG):
            return ''
        kwargs = {'datafile_id': self.id}
        return reverse('view_datafile', kwargs=kwargs)

    def get_download_url(self):
        view = ''
        kwargs = {'datafile_id': self.id}

        # these are the internally known protocols
        protocols = ['', 'tardis', 'file', 'http', 'https', 'ftp']
        if self.protocol in protocols:
            view = 'tardis.tardis_portal.download.download_datafile'

        # externally handled protocols
        else:
            try:
                for module in settings.DOWNLOAD_PROVIDERS:
                    if module[0] == self.protocol:
                        view = '%s.download_datafile' % module[1]
            except AttributeError:
                pass

        if view:
            return reverse(view, kwargs=kwargs)
        else:
            return ''

    def get_relative_filepath(self):
        if self.protocol == '' or self.protocol == 'tardis':
            from os.path import abspath, join
            return abspath(join(self.url.partition('://')[2]))
        elif self.protocol == 'staging':
            return self.url
        # file should refer to an absolute location
        elif self.protocol == 'file':
            return self.url.partition('://')[2]

    def get_absolute_filepath(self):
        # check for empty protocol field (historical reason) or
        # 'tardis' which indicates a location within the tardis file
        # store
        if self.protocol == '' or self.protocol == 'tardis':
            try:
                FILE_STORE_PATH = settings.FILE_STORE_PATH
            except AttributeError:
                return ''

            raw_path = self.url.partition('://')[2]
            # Standard location for local files
            file_path = path.abspath(path.join(FILE_STORE_PATH,
                                               str(self.dataset.experiment.id),
                                               str(self.dataset.id),
                                               raw_path))
            if path.isfile(file_path):
                return file_path
            # Legacy location for local files
            file_path = path.abspath(path.join(FILE_STORE_PATH,
                                               str(self.dataset.experiment.id),
                                               raw_path))
            if path.isfile(file_path):
                return file_path
            return ''
        elif self.protocol == 'staging':
            return self.url
        # file should refer to an absolute location
        elif self.protocol == 'file':
            return self.url.partition('://')[2]
        # ok, it doesn't look like the file is stored locally
        else:
            return ''

    def _set_size(self):

        from os.path import getsize
        self.size = str(getsize(self.get_absolute_filepath()))

    def _set_mimetype(self):

        try:
            from magic import Magic
        except:
            # TODO log that this failed
            return
        self.mimetype = Magic(mime=True).from_file(
            self.get_absolute_filepath())

    def _set_md5sum(self):

        f = open(self.get_absolute_filepath(), 'rb')
        import hashlib
        md5 = hashlib.new('md5')
        for chunk in iter(lambda: f.read(128 * md5.block_size), ''):
            md5.update(chunk)
        f.close()
        self.md5sum = md5.hexdigest()

    def deleteCompletely(self):
        import os
        filename = self.get_absolute_filepath()
        os.remove(filename)
        self.delete()


def save_DatasetFile(sender, **kwargs):

    # the object can be accessed via kwargs 'instance' key.
    df = kwargs['instance']

    if not df.get_absolute_filepath():
        return

    try:
        if not df.size:
            df._set_size()
        if not df.md5sum:
            df._set_md5sum()
        if not df.mimetype:
            df._set_mimetype()

    except IOError:
        pass
    except OSError:
        pass


pre_save.connect(save_DatasetFile, sender=Dataset_File)
