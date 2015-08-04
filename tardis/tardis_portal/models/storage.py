import os
from os import path
import random

from django.conf import settings
from django.db import models
from django.db.utils import DatabaseError
import django.core.files.storage as django_storage

from celery.contrib.methods import task

import logging
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
    max_size = models.BigIntegerField()  # Bytes
    status = models.CharField(max_length=100)
    name = models.TextField(default='default', unique=True)
    description = models.TextField(default='Default Storage')
    master_box = models.ForeignKey('self', null=True, blank=True,
                                   related_name='child_boxes')

    # state values for different types of storage:
    DISK = 1
    TAPE = 2
    CACHE = 3
    TEMPORARY = 4
    TYPE_UNKNOWN = 5
    # end state values

    # translate type attributes to constants
    TYPES = {
        'cache': CACHE,
        'receiving': TEMPORARY,
        'tape': TAPE,
    }

    # storage types that provide instantaneous access
    online_types = [CACHE,
                    DISK,
                    TEMPORARY]

    # when file access is requested, try in this order
    type_order = [CACHE,
                  DISK,
                  TAPE,
                  TEMPORARY,
                  TYPE_UNKNOWN]

    def __unicode__(self):
        return self.name or "anonymous Storage Box"

    @property
    def storage_type(self):
        try:
            storage_type = self.attributes.get(key='type').value
            return StorageBox.TYPES.get(
                storage_type, StorageBox.TYPE_UNKNOWN)
        except StorageBoxAttribute.DoesNotExist:
            return StorageBox.TYPE_UNKNOWN

    def get_options_as_dict(self):
        opts_dict = {}
        # using ugly for loop for python 2.6 compatibility
        for o in self.options.all():
            opts_dict[o.key] = o.value
        return opts_dict

    def get_initialised_storage_instance(self):
        storage_class = django_storage.get_storage_class(
            self.django_storage_class)
        return storage_class(**self.get_options_as_dict())

    class Meta:
        app_label = 'tardis_portal'
        verbose_name_plural = 'storage boxes'

    @property
    def cache_box(self):
        """
        Get cache box if set up
        """
        caches = [box for box in self.child_boxes.all()
                  if box.storage_type == StorageBox.CACHE]
        if len(caches) == 1:
            return caches[0]
        elif len(caches) > 1:
            return caches[random.choice(range(len(caches)))]
        else:
            return None

    @task(name="tardis_portal.storage_box.copy_files", ignore_result=True)
    def copy_files(self, dest_box=None):
        for dfo in self.file_objects.all():
            dfo.copy_file(dest_box)

    @task(name="tardis_portal.storage_box.move_files", ignore_result=True)
    def move_files(self, dest_box=None):
        for dfo in self.file_objects.all():
            dfo.move_file(dest_box)

    @task(name='tardis_portal.storage_box.copy_to_master')
    def copy_to_master(self):
        if getattr(self, 'master_box'):
            self.copy_files(self.master_box)

    @task(name='tardis_portal.storage_box.move_to_master')
    def move_to_master(self):
        if getattr(self, 'master_box'):
            self.move_files(self.master_box)

    @classmethod
    def get_default_storage(cls, location=None, user=None):
        '''
        gets first storage box or get local storage box with given base
        location or create one if it doesn't exist.

        get largest free space one

        test for authorisation
        '''
        if location is not None:
            try:
                return StorageBox.objects.get(options__key='location',
                                              options__value=location)
            except StorageBox.DoesNotExist:
                return StorageBox.create_local_box(location)
        try:
            # TODO: test for authorisation,
            # e.g. user.has_perm('storage_box.write', box)
            # TODO: check for free space, e.g. run SQL as on stats page to
            # get total size on box,
            # compute max(list, key=lambda x:max_size-size)
            return StorageBox.objects.all()[0]
        except (DatabaseError, IndexError):
            default_location = getattr(settings, "DEFAULT_STORAGE_BASE_DIR",
                                       '/var/lib/mytardis/store')
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
    simple key: value store
    '''

    storage_box = models.ForeignKey(StorageBox, related_name='options')
    key = models.TextField()
    value = models.TextField()

    def __unicode__(self):
        return '-> '.join([
            self.storage_box.__unicode__(),
            ': '.join([self.key or 'no key', self.value or 'no value'])
        ])

    class Meta:
        app_label = 'tardis_portal'


class StorageBoxAttribute(models.Model):
    '''
    can hold attributes/metadata about different storage locations.

    built-ins:
    key   values      description
    type  receiving   holds files temporarily for ingestion only
          permanent   permanent location (assumed by default)
          cache       holds files for fast access
    '''

    storage_box = models.ForeignKey(StorageBox, related_name='attributes')
    key = models.TextField()
    value = models.TextField()

    def __unicode__(self):
        return '-> '.join([
            self.storage_box.__unicode__(),
            ': '.join([self.key or 'no key', self.value or 'no value'])
        ])

    class Meta:
        app_label = 'tardis_portal'
