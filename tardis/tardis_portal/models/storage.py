from os import path

from django.conf import settings
from django.db import models
from django.db.utils import DatabaseError
import django.core.files.storage as django_storage


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
            base_location = getattr(settings, "DEFAULT_STORAGE_BASE_DIR",
                                    '/var/lib/mytardis/store')
            path.join(
                base_location,
                dfo.datafile.dataset.directory,
                dfo.datafile.dataset.description,
                dfo.datafile.directory,
                dfo.datafile.filename)

        build_save_location = getattr(
            self.get_initialised_storage_instance(),
            'build_save_location',
            default_save_location)
        return build_save_location(dfo)

    class Meta:
        app_label = 'tardis_portal'
        verbose_name_plural = 'storage boxes'

    @classmethod
    def get_default_storage(cls):
        try:
            return StorageBox.objects.all()[0]
        except (DatabaseError, IndexError):
            return None


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
