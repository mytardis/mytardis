from os import path
from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.core.files import File
from django.core.urlresolvers import reverse

from celery.contrib.methods import task

from tardis.tardis_portal.util import generate_file_checksums

from .fields import DirectoryField
from .dataset import Dataset
from .storage import StorageBox

import logging
logger = logging.getLogger(__name__)

IMAGE_FILTER = (Q(mimetype__startswith='image/') &
                ~Q(mimetype='image/x-icon')) |\
    (Q(datafileparameterset__datafileparameter__name__units__startswith="image"))  # noqa


class DataFile(models.Model):
    """Class to store meta-data about a file.  The physical copies of a
    file are described by distinct DataFileObject instances.

    :attribute dataset: the foreign key to the
       :class:`tardis.tardis_portal.models.Dataset` the file belongs to.
    :attribute filename: the name of the file, excluding the path.
    :attribute size: the size of the file.
    :attribute created_time: time the file was added to tardis
    :attribute modification_time: last modification time of the file
    :attribute mimetype: for example 'application/pdf'
    :attribute md5sum: digest of length 32, containing only hexadecimal digits
    :attribute sha512sum: digest of length 128, containing only hexadecimal
        digits
    """

    dataset = models.ForeignKey(Dataset)
    filename = models.CharField(max_length=400)
    directory = DirectoryField(blank=True, null=True)
    size = models.CharField(blank=True, max_length=400)
    created_time = models.DateTimeField(null=True, blank=True)
    modification_time = models.DateTimeField(null=True, blank=True)
    mimetype = models.CharField(blank=True, max_length=80)
    md5sum = models.CharField(blank=True, max_length=32)
    sha512sum = models.CharField(blank=True, max_length=128)
    deleted = models.BooleanField(default=False)
    deleted_time = models.DateTimeField(blank=True, null=True)
    version = models.IntegerField(default=1)

    @property
    def file_object(self):
        dfos = DataFileObject.objects.filter(datafile=self)
        return self.file_objects.get(
            storage_box=dfos[0].storage_box).file_object

    @file_object.setter
    def file_object(self, file_object):
        '''
        replace contents of file in all its locations
        '''
        oldobjs = []
        if self.file_objects.count() > 0:
            oldobjs = list(self.file_objects.all())
        if self.dataset.storage_boxes.count() == 0:
            self.dataset.storage_boxes.add(
                StorageBox.get_default_storage())
        for storage_box in self.dataset.storage_boxes.all():
            newfile = DataFileObject(datafile=self,
                                     storage_box=storage_box)
            newfile.save()
            newfile.file_object = file_object
            newfile.verify.delay()
        if len(oldobjs) > 0:
            for obj in oldobjs:
                obj.delete()

    class Meta:
        app_label = 'tardis_portal'
        ordering = ['filename']
        unique_together = ['dataset', 'directory', 'filename', 'version']

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
        require_checksums = kwargs.pop('require_checksums', True)
        if settings.REQUIRE_DATAFILE_CHECKSUMS and \
                not self.md5sum and not self.sha512sum and require_checksums:
            raise Exception('Every Datafile requires a checksum')
        elif settings.REQUIRE_DATAFILE_SIZES and \
                not self.size:
            raise Exception('Every Datafile requires a file size')
        super(DataFile, self).save(*args, **kwargs)

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
                return mimetypes.types_map[suffix.lower()]
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
        return '/api/v1/dataset_file/%d/download' % self.id

    def get_file(self):
        return self.file_object

    def get_absolute_filepath(self):
        dfo = self.default_dfo
        if dfo is not None:
            return dfo.get_full_path()
        else:
            return None

    def get_file_getter(self):
        return self.default_dfo.get_file_getter()

    def is_local(self):
        return self.default_dfo.is_local()

    def has_image(self):
        from .parameters import DatafileParameter

        if self.is_image():
            return True

        # look for image data in parameters
        pss = self.getParameterSets()

        if not pss:
            return False

        for ps in pss:
            dps = DatafileParameter.objects.filter(
                parameterset=ps, name__data_type=5,
                name__units__startswith="image")

            if len(dps):
                return True

        return False

    def is_image(self):
        '''
        returns True if it's an image and not an x-icon and not an img
        the image/img mimetype is made up though and may need revisiting if
        there is an official img mimetype that does not refer to diffraction
        images
        '''
        mimetype = self.get_mimetype()
        return mimetype.startswith('image/') \
            and mimetype not in ('image/x-icon', 'image/img')

    def get_image_data(self):
        from .parameters import DatafileParameter

        if self.is_image():
            return self.get_file()

        # look for image data in parameters
        pss = self.getParameterSets()

        if not pss:
            return None

        for ps in pss:
            dps = DatafileParameter.objects.filter(
                parameterset=ps, name__data_type=5,
                name__units__startswith="image")

            if len(dps):
                preview_image_par = dps[0]

        if preview_image_par:
            file_path = path.abspath(path.join(settings.METADATA_STORE_PATH,
                                               preview_image_par.string_value))

            preview_image_file = file(file_path)

            return preview_image_file

        else:
            return None

    def is_public(self):
        from .experiment import Experiment
        return Experiment.objects.filter(
            datasets=self.dataset,
            public_access=Experiment.PUBLIC_ACCESS_FULL).exists()

    def _has_any_perm(self, user_obj):
        if not hasattr(self, 'id'):
            return False
        return self.dataset

    def _has_view_perm(self, user_obj):
        return self._has_any_perm(user_obj)

    def _has_change_perm(self, user_obj):
        return self._has_any_perm(user_obj)

    def _has_delete_perm(self, user_obj):
        return self._has_any_perm(user_obj)

    @property
    def default_dfo(self):
        s_box = self.dataset.get_default_storage_box()
        try:
            return self.file_objects.get(storage_box=s_box)
        except DataFileObject.DoesNotExist:
            return None

    @property
    def verified(self):
        return all([obj.verified for obj in self.file_objects.all()])

    def verify(self, reverify=False):
        return all([obj.verify() for obj in self.file_objects.all()
                    if reverify or not obj.verified])


class DataFileObject(models.Model):
    '''
    holds one copy of the data for a datafile
    '''

    datafile = models.ForeignKey(DataFile, related_name='file_objects')
    storage_box = models.ForeignKey(StorageBox, related_name='file_objects')
    uri = models.TextField(blank=True, null=True)  # optional
    created_time = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    last_verified_time = models.DateTimeField(blank=True, null=True)

    _cached_file_object = None

    class Meta:
        app_label = 'tardis_portal'
        unique_together = ['datafile', 'storage_box']

    def _get_default_storage_class(self):
        return self.datafile.dataset.get_fastest_storage_box()

    def _get_identifier(self):
        '''
        the default identifier would be directory and file name, but it may
        not work for all backends. This function aims to abstract it.
        '''

        def default_identifier(dfo):
            if dfo.uri is None:
                path_parts = ["%s-%s" % (dfo.datafile.dataset.description
                                         or 'untitled',
                                         dfo.datafile.dataset.id)]
                if dfo.datafile.directory is not None:
                    path_parts += [dfo.datafile.directory]
                path_parts += [dfo.datafile.filename]
                dfo.uri = path.join(*path_parts)
                dfo.save()
            return dfo.uri

        build_identifier = getattr(
            self.storage_box.get_initialised_storage_instance(),
            'build_identifier',
            default_identifier)
        return build_identifier(self)

    def get_save_location(self):
        return self.storage_box.get_save_location(self)

    @property
    def file_object(self):
        '''
        a set of accessor functions that convert the file information to a
        standard python file object for reading and copy the contents of an
        existing file_object into the storage backend.
        '''
        if self._cached_file_object is None or self._cached_file_object.closed:
            self._cached_file_object = self\
                .storage_box.get_initialised_storage_instance().open(
                    self._get_identifier())
        return self._cached_file_object

    @file_object.setter
    def file_object(self, file_object):
        '''
        write contents of file object to storage_box
        '''
        if file_object.closed:
            file_object = File(file_object)
            file_object.open()
        file_object.seek(0)
        self.uri = self.storage_box.get_initialised_storage_instance()\
                                   .save(self._get_identifier(), file_object)
        self.save()

    @property
    def size(self):
        return self.storage_box.get_initialised_storage_instance().size(
                    self._get_identifier())

    def delete(self):
        super(DataFileObject, self).delete()

    @task(name="tardis_portal.verify_dfo_method", ignore_result=True)
    def verify(self, tempfile=None):  # too complex # noqa
        '''
        If passed a file handle, it will write the file to it instead
        of discarding data as it's read.
        '''
        allowEmptyChecksums = not getattr(settings,
                                          "REQUIRE_DATAFILE_CHECKSUMS", True)
        df = self.datafile
        if not (allowEmptyChecksums or df.sha512sum or df.md5sum):
            logger.error("Datafile for %s has no checksums", self.uri)
            return False
        try:
            file_object = self.file_object
        except IOError:
            logger.error("DFO %d not found/accessible at: %s" %
                         (self.id, self.uri))
            return False

        df_size = self.datafile.size
        if df_size is None or df_size == '':
            self.datafile.size = self.size
            self.datafile.save()
        elif int(df_size) != self.size:
            logger.error('DataFileObject with id %d did not verify. '
                         'File sizes did not match' % self.id)
            return False

        md5, sha512, size, mimetype_buffer = generate_file_checksums(
            self.file_object, tempfile)
        df_md5 = self.datafile.md5sum
        df_sha512 = self.datafile.sha512sum
        if df_sha512 is None or df_sha512 == '':
            if md5 != df_md5:
                logger.error('DataFileObject with id %d did not verify. '
                             'MD5 sums did not match' % self.id)
                return False
            self.datafile.sha512sum = sha512
            self.datafile.save()
        elif df_md5 is None or df_md5 == '':
            if sha512 != df_sha512:
                logger.error('DataFileObject with id %d did not verify. '
                             'SHA512 sums did not match' % self.id)
                return False
            self.datafile.md5sum = md5
            self.datafile.save()
        else:
            if not (md5 == df_md5 and sha512 == df_sha512):
                logger.error('DataFileObject with id %d did not verify. '
                             'Checksums did not match' % self.id)
                return False

        self.verified = True
        self.last_verified_time = datetime.now()
        self.save(update_fields=['verified', 'last_verified_time'])
        return True

    def get_full_path(self):
        return self.storage_box.get_initialised_storage_instance().path(
            self.uri)
