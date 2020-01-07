import hashlib
import logging
import re
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from urllib.parse import quote

from os import path
import mimetypes
import magic

import xxhash

from django.conf import settings
from django.core.files import File
from django.urls import reverse
from django.db import models
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from tardis.celery import tardis_app
from ..util import get_verify_priority
from .. import tasks
from .dataset import Dataset
from .storage import StorageBox, StorageBoxOption, StorageBoxAttribute

logger = logging.getLogger(__name__)

IMAGE_FILTER = (Q(mimetype__startswith='image/') &
                ~Q(mimetype='image/x-icon')) |\
    (Q(datafileparameterset__datafileparameter__name__units__startswith="image"))  # noqa


@python_2_unicode_compatible
class DataFile(models.Model):
    """A ``DataFile`` is a record of a file which includes its filename,
    its size in bytes, its relative directory, and various other meta-data.
    Each ``DataFile`` belongs to a
    :class:`~tardis.tardis_portal.models.dataset.Dataset` which usually
    represents the files from one folder on an instrument PC.

    The physical copy (or copies) of a file are described by distinct
    :class:`~tardis.tardis_portal.models.datafile.DataFileObject` records.

    :attribute dataset: The foreign key to the
       :class:`tardis.tardis_portal.models.Dataset` the file belongs to.
    :attribute filename: The name of the file, excluding the path.
    :attribute size: The size of the file.
    :attribute created_time: Should be populated with the file's creation time
      from the instrument PC.
    :attribute modification_time: Should be populated with the file's last
      modification time from the instrument PC.
    :attribute mimetype: For example 'application/pdf'
    """

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    filename = models.CharField(max_length=400)
    directory = models.CharField(blank=True, null=True, max_length=255)
    size = models.BigIntegerField(blank=True, null=True)
    created_time = models.DateTimeField(null=True, blank=True)
    modification_time = models.DateTimeField(null=True, blank=True)
    mimetype = models.CharField(db_index=True, blank=True, max_length=80)
    md5sum = models.CharField(blank=True, max_length=32)
    sha512sum = models.CharField(blank=True, max_length=128)
    algorithm = models.CharField(blank=True, max_length=6)
    checksum = models.CharField(blank=True, max_length=128)
    deleted = models.BooleanField(default=False)
    deleted_time = models.DateTimeField(blank=True, null=True)
    version = models.IntegerField(default=1)

    @property
    def file_object(self):
        return self.get_file()

    @file_object.setter
    def file_object(self, file_object):
        """
        Replace contents of file in all its locations
        TODO: new content implies new size and checksum. Are we going to
        auto-generate these or not allow this kind of assignment ?

        :type file_object: Python File object
        """
        oldobjs = []
        if self.file_objects.count() > 0:
            oldobjs = list(self.file_objects.all())
        s_boxes = [obj.storage_box for obj in oldobjs]
        if not s_boxes:
            s_boxes = [self.get_default_storage_box()]
        for box in s_boxes:
            newfile = DataFileObject(datafile=self,
                                     storage_box=box)
            newfile.save()
            newfile.file_object = file_object
        if oldobjs:
            for obj in oldobjs:
                obj.delete()

    @property
    def status(self):
        """
        returns information about the status of the file.
        States are defined in StorageBox
        """
        return {dfo.storage_type
                for dfo in self.file_objects.filter(verified=True)}

    @property
    def is_online(self):
        """
        return False if a file is on tape.
        At this stage it checks it returns true for no file objects, because
        those files are offline through other checks
        """
        dfos = self.file_objects.filter(verified=True)
        if dfos.count() == 0:
            return True
        return any(dfo.storage_type not in StorageBox.offline_types
                   for dfo in dfos)

    def cache_file(self):
        if self.is_online:
            return True
        for dfo in self.file_objects.filter(verified=True):
            if dfo.cache_file():
                return True
        return False

    def get_default_storage_box(self):
        '''
        try to guess appropriate box from dataset or use global default
        '''
        if settings.REUSE_DATASET_STORAGE_BOX:
            dataset_boxes = self.dataset.get_all_storage_boxes_used()
            if dataset_boxes.count() == 1:
                return dataset_boxes[0]
        # TODO: select one accessible to the owner of the file
        return StorageBox.get_default_storage()

    def get_receiving_storage_box(self):
        default_box = self.get_default_storage_box()
        child_boxes = [
            box for box in default_box.child_boxes.all()
            if box.attributes.filter(
                key="type", value="receiving").count() == 1]
        if child_boxes:
            return child_boxes[0]

        loc_boxes = StorageBoxOption.objects.filter(
            key='location',
            value=getattr(settings, 'DEFAULT_RECEIVING_DIR', '/tmp'))\
            .values_list('storage_box', flat=True)
        attr_boxes = StorageBoxAttribute.objects.filter(
            key="type", value="receiving")\
            .values_list('storage_box', flat=True)
        existing_default = set(loc_boxes) & set(attr_boxes)
        if existing_default:
            return StorageBox.objects.get(id=existing_default.pop())

        new_box = StorageBox.create_local_box(
            location=getattr(settings, 'DEFAULT_RECEIVING_DIR', '/tmp'))
        new_attr = StorageBoxAttribute(storage_box=new_box,
                                       key='type', value='receiving')
        new_attr.save()
        new_box.attributes.add(new_attr)
        new_box.master_box = default_box
        new_box.save()
        return new_box

    class Meta:
        app_label = 'tardis_portal'
        ordering = ['filename']
        unique_together = ['dataset', 'directory', 'filename', 'version']

    @classmethod
    def sum_sizes(cls, datafiles):
        """
        Takes a query set of datafiles and returns their total size.
        """
        return datafiles.aggregate(size=Sum('size'))['size'] or 0

    def save(self, *args, **kwargs):
        if self.size is not None:
            self.size = int(self.size)

        require_checksum = kwargs.pop('require_checksum', True)
        if settings.REQUIRE_DATAFILE_CHECKSUMS and require_checksum and \
                not self.algorithm and \
                not self.checksum:
            raise Exception('Every Datafile requires a checksum')
        if settings.REQUIRE_DATAFILE_SIZES:
            if self.size < 0:
                raise Exception('Invalid Datafile size (must be >= 0): %d' %
                                self.size)
        self.update_mimetype(save=False)

        super(DataFile, self).save(*args, **kwargs)

    def get_size(self):
        return self.size

    def getParameterSets(self):
        """Return datafile parametersets associated with this datafile.
        """
        from .parameters import Schema
        return self.datafileparameterset_set.filter(
            schema__type=Schema.DATAFILE)

    def __str__(self):
        return "%s(%s) %s # %s" % (self.algorithm, self.checksum,
                                   self.filename, self.mimetype)

    def get_mimetype(self):
        if self.mimetype:
            return self.mimetype
        suffix = path.splitext(self.filename)[-1]
        try:
            return mimetypes.types_map[suffix.lower()]
        except KeyError:
            return 'application/octet-stream'

    def get_view_url(self):
        render_image_size_limit = getattr(settings, 'RENDER_IMAGE_SIZE_LIMIT',
                                          0)
        if render_image_size_limit:
            if self.size > render_image_size_limit:
                return None

        viewable_mimetype_patterns = ('image/.*', 'text/.*', 'application/pdf')
        if not any(re.match(p, self.get_mimetype())
                   for p in viewable_mimetype_patterns):
            return None
        return reverse('tardis.tardis_portal.download.view_datafile',
                       kwargs={'datafile_id': self.id})

    def get_download_url(self):
        return reverse('api_download_file',
                       kwargs={'pk': self.id,
                               'api_name': 'v1',
                               'resource_name': 'dataset_file'})

    def get_file(self, verified_only=True):
        """
        Returns the file as a readable file-like object from the best avaiable
        storage box.

        If verified_only=False, the return of files without a verified checksum
        is allowed, otherwise None is returned for unverified files.

        :param bool verified_only: if False return files without verified
             checksum
        :returns: Python file object
        :rtype: Python File object
        """

        dfo = self.get_preferred_dfo(verified_only)
        if dfo is None:
            return None
        if dfo.storage_type in (StorageBox.TAPE,):
            shadow = 'dfo_cache_file location:%s' % dfo.storage_box.name
            tasks.dfo_cache_file.apply_async(
                args=[dfo.id], priority=dfo.priority, shadow=shadow)
        return dfo.file_object

    def get_preferred_dfo(self, verified_only=True):
        if verified_only:
            obj_query = self.file_objects.filter(verified=True)
        else:
            obj_query = self.file_objects.all()
        all_objs = {dfo.storage_type: dfo for dfo in obj_query}
        if not all_objs:
            return None
        dfo = None
        for dfo_type in StorageBox.type_order:
            dfo = all_objs.get(dfo_type, None)
            if dfo:
                break
        if not dfo:
            dfo = all_objs.values()[0]
        return dfo

    def get_absolute_filepath(self):
        dfos = self.file_objects.all()
        if dfos:
            return dfos[0].get_full_path()
        return None

    @contextmanager
    def get_as_temporary_file(self, directory=None):
        """Returns a traditional file-system-based file object
        that is a copy of the original data. The file is deleted
        when the context is destroyed.

        :param basestring directory: the directory in which to create the temp
            file
        :return: the temporary file object
        :rtype: NamedTemporaryFile
        """
        temp_file = NamedTemporaryFile(delete=True, dir=directory)
        try:
            temp_file.write(self.file_object.read())
            temp_file.flush()
            temp_file.seek(0, 0)
            yield temp_file
        finally:
            temp_file.close()

    def is_local(self):
        return self.file_objects.all()[0].is_local()

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

            if dps:
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
        from .parameters import DatafileParameter, ParameterName

        # look for image data in parameters
        preview_image_par = None
        pss = self.getParameterSets()

        for ps in pss:
            dps = DatafileParameter.objects.filter(
                parameterset=ps, name__data_type=ParameterName.FILENAME,
                name__units__startswith="image")

            if dps:
                preview_image_par = dps[0]

        if preview_image_par:
            file_path = path.abspath(path.join(settings.METADATA_STORE_PATH,
                                               preview_image_par.string_value))

            if path.exists(file_path):
                preview_image_file = open(file_path)
                return preview_image_file

        render_image_size_limit = getattr(settings, 'RENDER_IMAGE_SIZE_LIMIT',
                                          0)
        if self.is_image() and (self.size <= render_image_size_limit or
                                render_image_size_limit == 0):
            return self.get_file()

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

    def update_mimetype(self, mimetype=None, force=False, save=True):
        if self.mimetype is not None and self.mimetype != '' and not force:
            return self.mimetype
        fo = self.file_object
        if mimetype is None and fo is not None:
            m = magic.Magic(mime_and_encoding=True)
            mimetype = m.from_buffer(fo.read(1024))
            fo.close()
        if mimetype is None:
            mimetype, encoding = mimetypes.guess_type(self.filename)
            if mimetype is not None and encoding is not None:
                mimetype = '%s; %s' % (mimetype, encoding)
            mimetype = mimetype or 'application/octet-stream'
        if ';' in mimetype:
            mt, enc = mimetype.split(';')
            if enc.endswith('charset=binary'):
                mimetype = mt
        self.mimetype = mimetype
        if save:
            self.save()
        return mimetype

    @property
    def verified(self):
        """Return True if at least one DataFileObject is verified
        """
        dfos = [dfo.verified for dfo in self.file_objects.all()]
        return any(dfos)

    def verify(self, reverify=False):
        return all([obj.verify() for obj in self.file_objects.all()
                    if reverify or not obj.verified])


@python_2_unicode_compatible
class DataFileObject(models.Model):
    """The physical copy (or copies) of a
    :class:`~tardis.tardis_portal.models.datafile.DataFile`
    are described by distinct
    :class:`~tardis.tardis_portal.models.datafile.DataFileObject` records.

    :attribute datafile: The \
        :class:`~tardis.tardis_portal.models.datafile.DataFile` \
        record which this ``DataFileObject`` is storing a copy of.
    :attribute storage_box: The
        :class:`~tardis.tardis_portal.models.storage.StorageBox`
        containing this copy of the file.  The ``StorageBox`` could represent
        a directory on a mounted filesystem, or a bucket in an Object Store.
    :attribute uri: The relative path of the file location within the
        the :class:`~tardis.tardis_portal.models.storage.StorageBox`,
        e.g. ``dataset1-12345/file1.txt`` for a
        copy of a :class:`~tardis.tardis_portal.models.datafile.DataFile`
        with filename ``file1.txt`` which belongs to
        a :class:`~tardis.tardis_portal.models.dataset.Dataset`
        with a description of ``dataset1`` and an ID of ``12345``.
    """

    datafile = models.ForeignKey(DataFile, related_name='file_objects',
                                 on_delete=models.CASCADE)
    storage_box = models.ForeignKey(StorageBox, related_name='file_objects',
                                    on_delete=models.CASCADE)
    uri = models.TextField(blank=True, null=True)  # optional
    created_time = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    last_verified_time = models.DateTimeField(blank=True, null=True)

    _initial_values = None

    class Meta:
        app_label = 'tardis_portal'
        unique_together = ['datafile', 'storage_box']

    def __str__(self):
        try:
            return 'Box: %(storage_box)s, URI: %(uri)s, verified: %(v)s' % {
                'storage_box': str(self.storage_box),
                'uri': self.uri,
                'v': str(self.verified)
            }
        except:
            return 'undefined'

    def __init__(self, *args, **kwargs):
        """Stores values prior to changes for change detection in
        self._initial_values
        """
        super(DataFileObject, self).__init__(*args, **kwargs)
        self._initial_values = self._current_values

    @property
    def _current_values(self):
        return model_to_dict(self, fields=[
            field.name for field in self._meta.fields
            if field.name not in ['verified', 'last_verified_time']])

    @property
    def _changed(self):
        """return True if anything has changed since last save"""
        new_values = self._current_values
        for k, v in new_values.items():
            if k not in self._initial_values:
                return True
            if self._initial_values[k] != v:
                return True
        return False

    def save(self, *args, **kwargs):
        reverify = kwargs.pop('reverify', False)
        super(DataFileObject, self).save(*args, **kwargs)
        if self._changed:
            self._initial_values = self._current_values
        elif not reverify:
            return

        if self.uri is not None:
            verify_ms = getattr(settings, 'VERIFY_AS_SERVICE', False)
            try:
                if verify_ms:
                    tardis_app.send_task(
                        'verify_dfo',
                        args = [
                            self.id,
                            self.get_full_path(),
                            'save',
                            self.datafile.algorithm
                        ],
                        queue = 'verify',
                        priority = get_verify_priority(self.priority))
                else:
                    shadow = 'dfo_verify location:%s' % self.storage_box.name
                    tasks.dfo_verify.apply_async(
                        args=[self.id],
                        countdown=5,
                        priority=self.priority,
                        shadow=shadow)
            except Exception:
                logger.exception("Failed to verify file DFO ID %s", self.id)

    @property
    def storage_type(self):
        """
        :return: storage_box type
        :rtype: StorageBox type constant
        """
        return self.storage_box.storage_type

    def _create_uri(self):
        '''
        the default identifier would be directory and file name, but it may
        not work for all backends. This function aims to abstract it.
        '''

        def default_identifier(dfo):
            path_parts = ["%s-%s" % (
                quote(dfo.datafile.dataset.description, safe='') or 'untitled',
                dfo.datafile.dataset.id)]
            if dfo.datafile.directory is not None:
                path_parts += [quote(dfo.datafile.directory)]
            path_parts += [dfo.datafile.filename.strip()]
            uri = path.join(*path_parts)
            return uri

        # retained 'build_save_location' from earlier implementation
        # but it is deprecated. TODO: remove 'build_save_location' after
        # writing docs/changelog about its removal
        build_identifier = getattr(
            self._storage, 'build_identifier',
            getattr(self._storage, 'build_save_location',
                    lambda x: None))
        new_uri = build_identifier(self) or default_identifier(self)
        return new_uri

    def create_set_uri(self, force=False, save=False):
        """
        sets the uri as well as building it
        :param bool force:
        :param book save:
        :return:
        :rtype: basestring
        """
        if force or self.uri is None or self.uri.strip() != '':
            self.uri = self._create_uri()
            if save:
                self.save()
        return self.uri

    @property
    def file_object(self):
        """
        A set of accessor functions that convert the file information to a
        standard Python file object for reading and copy the contents of an
        existing file_object into the storage backend.

        :returns: a file object
        :rtype: Python File object
        """
        cached_file_object = getattr(self, '_cached_file_object', None)
        if cached_file_object is None or cached_file_object.closed:
            cached_file_object = self._storage.open(self.uri or
                                                    self._create_uri(),
                                                    mode='rb')
            self._cached_file_object = cached_file_object
        return self._cached_file_object

    @file_object.setter
    def file_object(self, file_object):
        """
        Write contents of file object to storage_box

        :type file_object: Python File object
        """
        if file_object.closed:
            file_object = File(file_object)
            file_object.open(mode='rb')
        file_object.seek(0)
        self.uri = self._storage.save(self.uri or self.create_set_uri(),
                                      file_object)  # TODO: define behaviour
        # when overwriting existing files
        file_object.close()
        self.verified = False
        self.save()

    @property
    def _storage(self):
        cached_storage = getattr(self, '_cached_storage', None)
        if cached_storage is None:
            cached_storage = self.storage_box\
                                 .get_initialised_storage_instance()
            self._cached_storage = cached_storage
        return self._cached_storage

    def cache_file(self):
        cache_box = self.storage_box.cache_box
        if cache_box is not None:
            return self.copy_file(cache_box)
        return None

    def copy_file(self, dest_box=None, verify=True):
        """
        copies verified file to new storage box
        checks for existing copy
        triggers async verification if not disabled
        :param StorageBox dest_box: StorageBox instance
        :param bool verify:
        :returns: DataFileObject of copy
        :rtype: DataFileObject
        """
        if not self.verified:
            logger.debug('DFO (id: %d) could not be copied.'
                         ' Source not verified' % self.id)
            return False
        if dest_box is None:
            dest_box = StorageBox.get_default_storage()
        existing = self.datafile.file_objects.filter(storage_box=dest_box)
        if existing.count() > 0:
            if not existing[0].verified and verify:
                verify_ms = getattr(settings, 'VERIFY_AS_SERVICE', False)
                try:
                    if verify_ms:
                        tardis_app.send_task(
                            'verify_dfo',
                            args = [
                                existing[0].id,
                                existing[0].get_full_path(),
                                'copy_file',
                                existing[0].datafile.algorithm
                            ],
                            queue = 'verify',
                            priority = get_verify_priority(existing[0].priority))
                    else:
                        shadow = 'dfo_verify location:%s' % existing[0].storage_box.name
                        tasks.dfo_verify.apply_async(
                            args=[existing[0].id],
                            priority=existing[0].priority,
                            shadow=shadow)
                except Exception:
                    logger.exception("Failed to verify file DFO ID %s", existing[0].id)
            return existing[0]
        try:
            with transaction.atomic():
                copy = DataFileObject(
                    datafile=self.datafile,
                    storage_box=dest_box)
                copy.save()
                copy.file_object = self.file_object
        except Exception as e:
            logger.error(
                'file copy failed for dfo id: %s, with error: %s' %
                (self.id, str(e)))
            return False
        if verify:
            verify_ms = getattr(settings, 'VERIFY_AS_SERVICE', False)
            try:
                if verify_ms:
                    tardis_app.send_task(
                        'verify_dfo',
                        args = [
                            copy.id,
                            copy.get_full_path(),
                            'copy_file',
                            copy.datafile.algorithm
                        ],
                        queue = 'verify',
                        priority = get_verify_priority(copy.priority))
                else:
                    shadow = 'dfo_verify location:%s' % copy.storage_box.name
                    tasks.dfo_verify.apply_async(
                        args=[copy.id],
                        priority=copy.priority,
                        shadow=shadow)
            except Exception:
                logger.exception("Failed to verify file DFO ID %s", copy.id)
        return copy

    def move_file(self, dest_box=None):
        """
        moves a file
        copies first, then synchronously verifies
        deletes file if copy is true copy and has been verified

        :param StorageBox dest_box: StorageBox instance
        :returns: moved file dfo
        :rtype: DataFileObject
        """
        copy = self.copy_file(dest_box=dest_box, verify=False)
        if copy and copy.id != self.id and (copy.verified or copy.verify()):
            self.delete()
        return copy

    def calculate_checksum(self, algorithm):
        """Calculates checksums for a DataFileObject instance

        :param algorithm: algorithm to use for checksum calculation
        :type algorithm: string

        :return: the checksum
        :rtype: string
        """
        from importlib import import_module

        storage_class_name = self.storage_box.django_storage_class
        calculate_checksum_methods = getattr(
            settings, 'CALCULATE_CHECKSUM_METHODS', {})
        if storage_class_name in calculate_checksum_methods:
            calculate_checksum_method = \
                calculate_checksum_methods[storage_class_name]
            module_path, method_name = calculate_checksum_method.rsplit('.', 1)
            module = import_module(module_path)
            calculate_checksum = getattr(module, method_name)
            return calculate_checksum(self, algorithm)

        return compute_checksum(self.file_object, algorithm)

    def verify(self):  # too complex # noqa
        df = self.datafile
        posted = len(getattr(df, 'algorithm')) == 0
        result = False
        try:
            fsize = self.file_object.size
            if posted:
                df.size = fsize
                df.algorithm = getattr(settings, 'VERIFY_DEFAULT_ALGORITHM', 'md5')
            checksum = self.calculate_checksum(df.algorithm)
            if posted:
                df.checksum = checksum
                df.save(update_fields=['size', 'algorithm', 'checksum'])
            result = (getattr(df, 'size') == fsize and
                getattr(df, 'checksum') == checksum)
            if not result:
                logger.error("Did not verify DFO={}".format(self.id))
        except IOError as e:
            logger.error("Can'\t verify DFO={}".format(self.id))
            logger.debug(str(e))
        self.verified = result
        self.last_verified_time = timezone.now()
        self.save(update_fields=['verified', 'last_verified_time'])
        df.update_mimetype()
        if result and getattr(settings, 'USE_FILTERS', False):
            self.apply_filters()
        return result

    def apply_filters(self):
        from django.core.files.storage import FileSystemStorage
        from django.core.files.storage import get_storage_class
        from tardis.celery import tardis_app

        storage_class = get_storage_class(self.storage_box.django_storage_class)
        if not issubclass(storage_class, FileSystemStorage):
            logger.debug(
		"Can't apply filters for DFO ID %s with storage class %s",
                self.id, self.storage_box.django_storage_class)
            return

        try:
            tardis_app.send_task(
                'apply_filters',
                args = [
                    self.datafile.id,
                    self.verified,
                    self.get_full_path(),
                    self.uri
                ],
                queue = 'filters',
                priority = getattr(settings, 'FILTERS_TASK_PRIORITY', 0))
        except Exception:
            logger.exception("Failed to apply filters for DFO ID %s", self.id)

    def get_full_path(self):
        return self._storage.path(self.uri)

    def delete_data(self):
        self._storage.delete(self.uri)

    @property
    def modified_time(self):
        return self._storage.get_modified_time(self.uri)

    @property
    def priority(self):
        '''
        Default priority for tasks which take this DFO as an argument
        '''
        return self.storage_box.priority


@receiver(pre_delete, sender=DataFileObject, dispatch_uid='dfo_delete')
def delete_dfo(sender, instance, **kwargs):
    '''
    Deletes the actual file / object, before deleting the database record
    '''
    can_delete = getattr(
        instance.storage_box.attributes.filter(key='can_delete').first(),
        'value', 'True')
    if can_delete.lower() == 'true' and instance.uri:
        try:
            instance.delete_data()
        except NotImplementedError:
            logger.info('deletion not supported on storage box %s, '
                        'for dfo id %s' % (str(instance.storage_box),
                                           str(instance.id)))
    elif not instance.uri:
        logger.warning('DFO %s has no URI, so no data to delete' % instance.id)
    else:
        logger.debug('Did not delete file dfo.id '
                     '%s, because deletes are disabled' % instance.id)


def compute_checksum(file_object, algorithm,
                     close_file=True, bs=0):
    """Computes checksum for a python file object

    :param object file_object: Python File object
    :param string algorithm: algorithm to use for checksum calculation
    :param bool close_file: whether to close the file_object, default=True
    :param int bs: file chunk size, default is set by hasher * 32

    :return: the checksum
    :rtype: string

    :raises NotImplementedError:
    """
    if algorithm == 'xxh32':
        hasher = xxhash.xxh32()
    elif algorithm == 'xxh64':
        hasher = xxhash.xxh64()
    elif algorithm in ('md5', 'sha512'):
        hasher = hashlib.new(algorithm)
    else:
        raise NotImplementedError
    chunksize = max(bs, hasher.block_size*32)
    file_object.seek(0)
    for chunk in iter(lambda: file_object.read(chunksize), b''):
        hasher.update(chunk)
    if close_file:
        file_object.close()
    else:
        file_object.seek(0)
    return hasher.hexdigest()
