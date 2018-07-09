# pylint: disable=R0916
# remove when file sizes are integers
import hashlib
import logging
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

from os import path
import mimetypes

from six.moves import urllib
from six import string_types

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

import magic

from .. import tasks
from .dataset import Dataset
from .storage import StorageBox, StorageBoxOption, StorageBoxAttribute

logger = logging.getLogger(__name__)

IMAGE_FILTER = (Q(mimetype__startswith='image/') &
                ~Q(mimetype='image/x-icon')) |\
    (Q(datafileparameterset__datafileparameter__name__units__startswith="image"))  # noqa


@python_2_unicode_compatible
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

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    filename = models.CharField(max_length=400)
    directory = models.CharField(blank=True, null=True, max_length=255)
    size = models.BigIntegerField(blank=True, null=True)
    created_time = models.DateTimeField(null=True, blank=True)
    modification_time = models.DateTimeField(null=True, blank=True)
    mimetype = models.CharField(db_index=True, blank=True, max_length=80)
    md5sum = models.CharField(blank=True, max_length=32)
    sha512sum = models.CharField(blank=True, max_length=128)
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
        TODO: new content implies new size and checksums. Are we going to
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
        try to guess appropriate box from files, dataset or experiment
        '''
        boxes_used = StorageBox.objects.filter(file_objects__datafile=self)
        if boxes_used:
            return boxes_used[0]
        dataset_boxes = self.dataset.get_all_storage_boxes_used()
        if dataset_boxes:
            return dataset_boxes[0]
        experiment_boxes = StorageBox.objects.filter(
            file_objects__datafile__dataset__experiments__in=self
            .dataset.experiments.all())
        if experiment_boxes:
            return experiment_boxes[0]
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

        require_checksums = kwargs.pop('require_checksums', True)
        if settings.REQUIRE_DATAFILE_CHECKSUMS and \
                not self.md5sum and \
                not self.sha512sum and \
                require_checksums:
            raise Exception('Every Datafile requires a checksum')
        elif settings.REQUIRE_DATAFILE_SIZES:
            if self.size < 0:
                raise Exception('Invalid Datafile size (must be >= 0): %d' %
                                self.size)
        self.update_mimetype(save=False)

        super(DataFile, self).save(*args, **kwargs)

    def get_size(self):
        return self.size

    def getParameterSets(self, schemaType=None):
        """Return datafile parametersets associated with this datafile.

        """
        from .parameters import Schema
        if schemaType == Schema.DATAFILE or schemaType is None:
            return self.datafileparameterset_set.filter(
                schema__type=Schema.DATAFILE)
        else:
            raise Schema.UnsupportedType

    def __str__(self):
        if self.sha512sum is not None and len(self.sha512sum) > 31:
            checksum = str(self.sha512sum)[:32]
        else:
            checksum = self.md5sum or 'no checksum'
        return "%s %s # %s" % (checksum,
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
        render_image_size_limit = getattr(settings, 'RENDER_IMAGE_SIZE_LIMIT',
                                          0)
        if render_image_size_limit:
            try:
                if self.size > render_image_size_limit:
                    return None
            except ValueError:
                return None

        import re
        viewable_mimetype_patterns = ('image/.*', 'text/.*', 'application/pdf')
        if not any(re.match(p, self.get_mimetype())
                   for p in viewable_mimetype_patterns):
            return None
        return reverse('view_datafile', kwargs={'datafile_id': self.id})

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
             checksums
        :returns: Python file object
        :rtype: Python File object
        """

        dfo = self.get_preferred_dfo(verified_only)
        if dfo is None:
            return None
        if dfo.storage_type in (StorageBox.TAPE,):
            tasks.dfo_cache_file.apply_async(args=[dfo.id])
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
        """
        Returns a traditional file-system-based file object
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
        from .parameters import DatafileParameter

        render_image_size_limit = getattr(settings, 'RENDER_IMAGE_SIZE_LIMIT',
                                          0)
        if self.is_image() and (self.size <= render_image_size_limit or
                                render_image_size_limit == 0):
            return self.get_file()

        # look for image data in parameters
        preview_image_par = None
        pss = self.getParameterSets()

        if not pss:
            return None

        for ps in pss:
            dps = DatafileParameter.objects.filter(
                parameterset=ps, name__data_type=5,
                name__units__startswith="image")

            if dps:
                preview_image_par = dps[0]

        if preview_image_par:
            file_path = path.abspath(path.join(settings.METADATA_STORE_PATH,
                                               preview_image_par.string_value))

            preview_image_file = open(file_path)

            return preview_image_file
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
    def verified(self, all_dfos=False):
        dfos = [dfo.verified for dfo in self.file_objects.all()]
        if all_dfos:
            return all(dfos)
        return any(dfos)

    def verify(self, reverify=False):
        return all([obj.verify() for obj in self.file_objects.all()
                    if reverify or not obj.verified])


@python_2_unicode_compatible
class DataFileObject(models.Model):
    '''
    holds one copy of the data for a datafile
    '''

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
        for k, v in new_values.iteritems():
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
        tasks.dfo_verify.apply_async(countdown=5, args=[self.id])

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
                urllib.parse.quote(dfo.datafile.dataset.description, safe='') or 'untitled',
                dfo.datafile.dataset.id)]
            if dfo.datafile.directory is not None:
                path_parts += [urllib.parse.quote(dfo.datafile.directory)]
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
                                                    self._create_uri())
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
            file_object.open()
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
                tasks.dfo_verify.delay(existing[0].id)
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
            tasks.dfo_verify.delay(copy.id)
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

    def verify(self, add_checksums=True, add_size=True):  # too complex # noqa
        comparisons = ['size', 'md5sum', 'sha512sum']

        df = self.datafile
        database = {comp_type: getattr(df, comp_type)
                    for comp_type in comparisons}
        database_update = {}
        empty_value = {db_key: db_val is None or (
            isinstance(db_val, string_types) and db_val.strip() == '')
            for db_key, db_val in database.items()}
        same_values = {key: False for key, empty in empty_value.items()
                       if not empty}
        io_error = False
        io_error_str = 'no error'
        actual = {}
        try:
            actual['size'] = self.file_object.size
            if not empty_value['size'] and \
               actual['size'] == database['size']:
                same_values['size'] = True
            elif empty_value['size']:
                # only ever empty when settings.REQ...SIZES = False
                if add_size:
                    database_update['size'] = actual['size']
            if same_values.get('size', True):
                compute_md5 = getattr(settings, 'COMPUTE_MD5', True)
                compute_sha512 = getattr(settings, 'COMPUTE_SHA512', True)
                actual.update(compute_checksums(
                    self.file_object,
                    compute_md5=compute_md5,
                    compute_sha512=compute_sha512))

                def collate_checksums(sum_type):
                    if empty_value[sum_type] and add_checksums:
                        # all sums only ever empty when not required
                        database_update[sum_type] = actual[sum_type]
                    if actual[sum_type] == database[sum_type]:
                        same_values[sum_type] = True

                if compute_md5:
                    collate_checksums('md5sum')
                if compute_sha512:
                    collate_checksums('sha512sum')

        except IOError as ioe:
            same_values = {key: False for key in same_values.keys()}
            io_error = True
            io_error_str = str(ioe)

        result = all(same_value for same_value in same_values.values())
        if result:
            if database_update:
                for key, val in database_update.items():
                    setattr(df, key, val)
                df.save()
        else:
            reasons = []
            if io_error:
                reasons = [io_error_str]
            else:
                for key, the_same in same_values.items():
                    if not the_same:
                        reasons.append(
                            '%s mismatch, database: %s, disk: %s.' % (
                                key, getattr(df, key),
                                actual.get(key, 'undefined')))
            logger.debug('DataFileObject with id %d did not verify. '
                         'Reasons: %s' %
                         (self.id, ' '.join(reasons)))

        self.verified = result
        self.last_verified_time = timezone.now()
        self.save(update_fields=['verified', 'last_verified_time'])
        df.update_mimetype()
        return result

    def get_full_path(self):
        return self._storage.path(self.uri)

    def delete_data(self):
        self._storage.delete(self.uri)

    @property
    def modified_time(self):
        return self._storage.get_modified_time(self.uri)


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


def compute_checksums(file_object,
                      compute_md5=True,
                      compute_sha512=True,
                      close_file=True):
    """Computes checksums for a python file object

    :param object file_object: Python File object
    :param compute_md5: whether to compute md5 default=True
    :type compute_md5: bool
    :param compute_sha512: whether to compute sha512, default=True
    :type compute_sha512: bool
    :param bool close_file: whether to close the file_object, default=True

    :return: the checksums as {'md5sum': result, 'sha512sum': result}
    :rtype: dict
    """
    blocksize = 0
    results = {}
    if compute_md5:
        md5_hasher = hashlib.new('md5')
        blocksize = max(md5_hasher.block_size, blocksize)
        results['md5sum'] = md5_hasher
    if compute_sha512:
        sha512_hasher = hashlib.new('sha512')
        blocksize = max(sha512_hasher.block_size, blocksize)
        results['sha512sum'] = sha512_hasher
    update_fns = {'md5sum': lambda x, y: x.update(y),
                  'sha512sum': lambda x, y: x.update(y)}
    file_object.seek(0)
    for chunk in iter(lambda: file_object.read(32 * blocksize), ''):
        for key, val in results.items():
            update_fns[key](val, chunk)
    if close_file:
        file_object.close()
    else:
        file_object.seek(0)
    final_fns = {'md5sum': lambda x: x.hexdigest(),
                 'sha512sum': lambda x: x.hexdigest()}
    return {key: final_fns[key](val) for key, val in results.items()}
