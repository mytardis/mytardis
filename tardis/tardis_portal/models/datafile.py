from os import path

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.core.urlresolvers import reverse

from .dataset import Dataset
from .replica import Replica

import logging
logger = logging.getLogger(__name__)

IMAGE_FILTER = (Q(mimetype__startswith='image/') & \
              ~Q(mimetype='image/x-icon')) | \
               (Q(datafileparameterset__datafileparameter__name__units__startswith="image"))

class Dataset_File(models.Model):
    """Class to store meta-data about a file.  The physical copies of a
    file are described by distinct Replica instances. 

    :attribute dataset: the foreign key to the
       :class:`tardis.tardis_portal.models.Dataset` the file belongs to.
    :attribute filename: the name of the file, excluding the path.
    :attribute size: the size of the file.
    :attribute created_time: time the file was added to tardis
    :attribute modification_time: last modification time of the file
    :attribute mimetype: for example 'application/pdf'
    :attribute md5sum: digest of length 32, containing only hexadecimal digits
    :attribute sha512sum: digest of length 128, containing only hexadecimal digits
    """

    dataset = models.ForeignKey(Dataset)
    filename = models.CharField(max_length=400)
    size = models.CharField(blank=True, max_length=400)
    created_time = models.DateTimeField(null=True, blank=True)
    modification_time = models.DateTimeField(null=True, blank=True)
    mimetype = models.CharField(blank=True, max_length=80)
    md5sum = models.CharField(blank=True, max_length=32)
    sha512sum = models.CharField(blank=True, max_length=128)

    class Meta:
        app_label = 'tardis_portal'
        ordering = ['filename']

    @classmethod
    def sum_sizes(cls, datafiles):
        """
        Takes a query set of datafiles and returns their total size.
        """
        def sum_str(*args):
            def coerce_to_long(x):
                try:
                    return long(x)
                except ValueError:
                    return 0
            return sum(map(coerce_to_long, args))
        # Filter empty sizes, get array of sizes, then reduce
        return reduce(sum_str, datafiles.exclude(size='')
                                        .values_list('size', flat=True), 0)

    def save(self, *args, **kwargs):
        if settings.REQUIRE_DATAFILE_CHECKSUMS and \
                not self.md5sum and not self.sha512sum:
            raise Exception('Every Datafile requires a checksum')
        elif settings.REQUIRE_DATAFILE_SIZES and \
                not self.size:
            raise Exception('Every Datafile requires a file size')
        else:
            super(Dataset_File, self).save(*args, **kwargs)
        
    def get_size(self):
        return self.size

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
        return "%s %s # %s" % (self.sha512sum[:32] or self.md5sum,
                               self.filename, self.mimetype)

    def get_mimetype(self):
        if self.mimetype:
            return self.mimetype
        else:
            suffix = path.splitext(self.filename)[-1]
            try:
                import mimetypes
                return mimetypes.types_map['.%s' % suffix.lower()]
            except KeyError:
                return 'application/octet-stream'

    def get_view_url(self):
        import re
        viewable_mimetype_patterns = ('image/.*', 'text/.*')
        if not any(re.match(p, self.get_mimetype())
                   for p in viewable_mimetype_patterns):
            return None
        return reverse('view_datafile', kwargs={'datafile_id': self.id})

    def get_download_url(self):
        replica = self.get_preferred_replica()
        if replica:
            return replica.get_download_url()
        else:
            return None
        
    def get_file(self):
        return self.get_preferred_replica().get_file()
        
    def get_absolute_filepath(self):
        return self.get_preferred_replica().get_absolute_filepath()

    def get_file_getter(self):
        return self.get_preferred_replica().get_file_getter()
        
    def is_local(self):
        return self.get_preferred_replica().is_local()
        
    def get_preferred_replica(self, verified=None):
        """Get the Datafile replica that is the preferred one for download.
        This entails fetching all of the Replicas and ordering by their
        respective Locations' computed priorities.  The 'verified' parameter
        allows you to select the preferred verified (or unverified) replica.
        """

        p = None
        if verified == None:
            replicas = Replica.objects.filter(datafile=self)
        else:
            replicas = Replica.objects.filter(datafile=self, verified=verified)
        for r in replicas: 
            if not p or \
                    p.location.get_priority() < r.location.get_priority():
                p = r
        # A datafile with no associated replicas is broken.
        if verified == None and not p:
            logger.error('Ooops! - Dataset_File %s has no replicas: %s', 
                         self.id, self)            
            if hasattr(settings, 'DEBUG') and settings.DEBUG:
                raise ValueError('Dataset_File has no replicas')
        return p

    def has_image(self):
        from .parameters import DatafileParameter
        
        if self.is_image():
            return True

        # look for image data in parameters
        pss = self.getParameterSets()
        
        if not pss:
            return False
        
        for ps in pss:
            dps = DatafileParameter.objects.filter(\
            parameterset=ps, name__data_type=5,\
            name__units__startswith="image")
            
            if len(dps):
                return True
        
        return False

    def is_image(self):
        return self.get_mimetype().startswith('image/') \
            and not self.get_mimetype() == 'image/x-icon'
            
    def get_image_data(self):
        from .parameters import DatafileParameter

        if self.is_image():
            return self.get_file()

        # look for image data in parameters
        pss = self.getParameterSets()

        if not pss:
            return None

        preview_image_data = None
        for ps in pss:
            dps = DatafileParameter.objects.filter(\
            parameterset=ps, name__data_type=5,\
            name__units__startswith="image")

            if len(dps):
                preview_image_par = dps[0]

        if preview_image_par:
            file_path = path.abspath(path.join(settings.FILE_STORE_PATH,
                                               preview_image_par.string_value))

            from django.core.servers.basehttp import FileWrapper
            preview_image_file = file(file_path)
            
            return preview_image_file
            
        else:
            return None

    def is_public(self):
        from .experiment import Experiment
        return Experiment.objects.filter(\
                  datasets=self.dataset,
                  public_access=Experiment.PUBLIC_ACCESS_FULL).exists()

