import base64
import os
import logging
import pickle
import random

from django.conf import settings
from django.db import models
from django.db.utils import DatabaseError
import django.core.files.storage as django_storage

#from celery.contrib.methods import task


logger = logging.getLogger(__name__)


class StorageBox(models.Model):
    '''
    table that holds storage boxes of any type.
    to extend to new types, add fields if necessary

    :attribute max_size: max size in bytes
    '''

    django_storage_class = models.TextField(
        default=getattr(settings, 'DEFAULT_FILE_STORAGE',
                        'django.core.files.storage.FileSystemStorage'))
    max_size = models.BigIntegerField(null=True, blank=True)  # Bytes
    status = models.CharField(max_length=100, default='online')
    name = models.CharField(max_length=255, default='default', unique=True)
    description = models.TextField(default='Default Storage')
    master_box = models.ForeignKey('self', null=True, blank=True,
                                   related_name='child_boxes',
                                   on_delete=models.CASCADE)

    # state values for different types of storage:
    DISK = 1
    TAPE = 2
    CACHE = 3
    TEMPORARY = 4
    TYPE_UNKNOWN = 5
    BUNDLE = 6
    # end state values

    # translate type attributes to constants
    TYPES = {
        'cache': CACHE,
        'receiving': TEMPORARY,
        'tape': TAPE,
        'disk': DISK,
        'bundle': BUNDLE,
    }

    # storage types that provide instantaneous access
    online_types = [CACHE,
                    DISK,
                    TEMPORARY,
                    BUNDLE]

    # storage types that do not provide instantaneous access
    offline_types = [TAPE, ]

    # when file access is requested, try in this order
    type_order = [CACHE,
                  BUNDLE,
                  DISK,
                  TAPE,
                  TEMPORARY,
                  TYPE_UNKNOWN]

    def __str__(self):
        return self.name or "anonymous Storage Box"

    @property
    def storage_type(self):
        try:
            storage_type = self.attributes.get(key='type').value
            return StorageBox.TYPES.get(
                storage_type, StorageBox.TYPE_UNKNOWN)
        except StorageBoxAttribute.DoesNotExist:
            return StorageBox.TYPE_UNKNOWN

    @property
    def autocache(self):
        """
        Whether to automatically copy data into faster storage

        :return: True if data should be automatically cached
        :rtype: bool
        """
        try:
            autocache_attr = self.attributes.get(key='autocache').value
            return autocache_attr.lower() == 'true'
        except StorageBoxAttribute.DoesNotExist:
            return False

    @property
    def priority(self):
        '''
        Default priority for tasks which take this box as an argument
        '''
        return int(getattr(
            self.attributes.filter(key='priority').first(),
            'value', settings.DEFAULT_TASK_PRIORITY))

    def get_options_as_dict(self):
        opts_dict = {}
        # using ugly for loop for python 2.6 compatibility
        for o in self.options.all():
            opts_dict[o.key] = o.unpickled_value
        return opts_dict

    def get_initialised_storage_instance(self):
        storage_class = django_storage.get_storage_class(
            self.django_storage_class)
        return storage_class(**self.get_options_as_dict())

    class Meta:
        app_label = 'tardis_portal'
        verbose_name_plural = 'storage boxes'
        ordering = ('name',)

    @property
    def cache_box(self):
        """
        Get cache box if set up
        """
        caches = [box for box in self.child_boxes.all()
                  if box.storage_type == StorageBox.CACHE]
        if len(caches) == 1:
            return caches[0]
        if len(caches) > 1:
            return caches[random.choice(range(len(caches)))]
        return None

    def copy_files(self, dest_box=None):
        for dfo in self.file_objects.all():
            dfo.copy_file(dest_box)

    def move_files(self, dest_box=None):
        for dfo in self.file_objects.all():
            dfo.move_file(dest_box)

    def copy_to_master(self):
        if getattr(self, 'master_box'):
            self.copy_files(self.master_box)

    def move_to_master(self):
        if getattr(self, 'master_box'):
            self.move_files(self.master_box)

    @classmethod
    def get_default_storage(cls, location=None, user=None):
        '''
        gets default storage box or get local storage box with given base
        location or create one if it doesn't exist.

        policies:
        Have a StorageBoxAttribute: key='default', value=True
        find a storage box where location is DEFAULT_STORAGE_BASE_DIR
        create a default storage box at DEFAULT_STORAGE_BASE_DIR
        lowest id storage box is default
        no storage box defined, use hard coded default for now  TODO: consider removing this

        Would be nice: get largest free space one, test for authorisation
        '''
        if location is None:
            try:
                # TODO: test for authorisation,
                # e.g. user.has_perm('storage_box.write', box)
                # TODO: check for free space, e.g. run SQL as on stats page to
                # get total size on box,
                # compute max(list, key=lambda x:max_size-size)
                return StorageBox.objects.get(attributes__key='default',
                                              attributes__value='True')
            except StorageBox.DoesNotExist:
                pass  # continue with other options
        default_location = getattr(settings, "DEFAULT_STORAGE_BASE_DIR", None)
        if location is not None or default_location is not None:
            box_location = location or default_location
            try:
                return StorageBox.objects.get(options__key='location',
                                              options__value=box_location)
            except StorageBox.DoesNotExist:
                return StorageBox.create_local_box(box_location)
        try:
            return StorageBox.objects.all().order_by('id')[0]
        except (DatabaseError, IndexError):
            default_location = '/var/lib/mytardis/store'
            return StorageBox.create_local_box(default_location)

    @classmethod
    def create_local_box(cls, location=None):
        try:
            base_dir_stat = os.statvfs(location)
        except OSError:
            logger.error('cannot access storage location: %s' % (location,))
            raise
        disk_size = base_dir_stat.f_frsize * base_dir_stat.f_blocks
        max_size = disk_size * 0.9
        s_box = StorageBox(name='local box at %s' % (location or
                           'default location'),
                           max_size=max_size,
                           status='online')
        s_box.save()
        sbo = StorageBoxOption(
            storage_box=s_box,
            key='location',
            value=location)
        sbo.save()
        return s_box


class StorageBoxOption(models.Model):
    '''
    holds the options passed to the storage class defined in StorageBox.
    key->value store with support for typed values through pickling when
    value_type is set to 'pickle'
    '''
    STRING = 'string'
    PICKLE = 'pickle'
    TYPE_CHOICES = ((STRING, 'String value'),
                    (PICKLE, 'Pickled value'))

    storage_box = models.ForeignKey(StorageBox, related_name='options',
                                    on_delete=models.CASCADE)
    key = models.TextField()
    value = models.TextField()
    value_type = models.CharField(max_length=6,
                                  choices=TYPE_CHOICES,
                                  default=STRING)

    def __str__(self):
        return '-> '.join([
            self.storage_box.__str__(),
            ': '.join([self.key or 'no key',
                       str(self.unpickled_value) or 'no value'])
        ])

    class Meta:
        app_label = 'tardis_portal'

    @property
    def unpickled_value(self):
        if not self.value or self.value == '':
            return None
        if self.value_type == StorageBoxOption.STRING:
            return self.value
        return pickle.loads(base64.b64decode(self.value))

    @unpickled_value.setter
    def unpickled_value(self, input_value):
        if self.value_type == StorageBoxOption.STRING:
            self.value = input_value
        else:
            self.value = base64.b64encode(pickle.dumps(input_value)).decode()


class StorageBoxAttribute(models.Model):
    '''
    Can hold attributes/metadata about different storage locations.

    :attribute key: The key used to look up the attribute (e.g. "type").
    :attribute value: The value of the attribute e.g. "cache".

    The "type" key has three values support by the core MyTardis
    code: "permanent", "receiving" and "cache".

    Adding an attribute with key "type" and value "permanent" preserves
    the default behaviour of a storage box, i.e. it is equivalent to
    not adding the attribute.

    Adding an attribute with key "type" and value "receiving" means
    that the storage box will be treated as a staging area which
    receives files intended to be transfered to a permanent storage
    box.  If a storage box has the "type: receiving" attribute,
    it must link to a permanent storage box (via its master_box foreign
    key).

    Adding an attribute with key "type" and value "cache" means that
    the storage box will be used to copy data from slow-access storage
    to fast-access storage.  If a storage box has the "type: cache"
    attribute, it must link to a permanent storage box (via its
    master_box foreign key).
    '''

    storage_box = models.ForeignKey(StorageBox, related_name='attributes',
                                    on_delete=models.CASCADE)
    key = models.TextField()
    value = models.TextField()

    def __str__(self):
        return '-> '.join([
            self.storage_box.__str__(),
            ': '.join([self.key or 'no key', self.value or 'no value'])
        ])

    class Meta:
        app_label = 'tardis_portal'
