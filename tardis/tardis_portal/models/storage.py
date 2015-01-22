import os
from os import path

from django.conf import settings
from django.db import models
from django.db.utils import DatabaseError
import django.core.files.storage as django_storage

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

    def __unicode__(self):
        return self.name or "anonymous Storage Box"

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

    def get_save_location(self, dfo):
        if self.attributes.filter(key="staging", value="True").count() == 0:
            return False

        def default_save_location(dfo):
            base_location = getattr(settings, "STAGING_PATH",
                                    '/var/lib/mytardis/staging')
            save_location = base_location
            if dfo.datafile.dataset.directory is not None:
                save_location = path.join(save_location,
                                          dfo.datafile.dataset.directory)
            save_location = path.join(save_location, dfo.datafile.dataset.description)
            if dfo.datafile.directory is not None:
                save_location = path.join(save_location,
                                          dfo.datafile.directory)
            save_location = path.join(save_location, dfo.datafile.filename)
            return save_location

        build_save_location = getattr(
            self.get_initialised_storage_instance(),
            'build_save_location',
            default_save_location)
        return build_save_location(dfo)

    class Meta:
        app_label = 'tardis_portal'
        verbose_name_plural = 'storage boxes'

    @classmethod
    def get_default_storage(cls, location=None):
        '''
        gets first storage box or get local storage box with given base
        location or create one if it doesn't exist.
        '''
        if location is not None:
            try:
                return StorageBox.objects.get(options__key='location',
                                              options__value=location)
            except StorageBox.DoesNotExist:
                return StorageBox.create_local_box(location)
        try:
            return StorageBox.objects.all().order_by('id')[0]
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
        s_box = StorageBox(max_size=max_size,
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
    Definitions are in documentation or per deployment.
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
