from django.db import models
import django.core.files.storage as django_storage


class StorageBox(models.Model):
    '''
    table that holds storage boxes of any type.
    to extend to new types, add fields if necessary

    :attribute max_size: max size in bytes
    '''

    django_storage_class = models.TextField()
    max_size = models.BigIntegerField()
    status = models.CharField(max_length=100)

    def get_options_as_dict(self):
        return {o.key: o.value for o in self.options.all()}

    def get_initialised_storage_instance(self):
        storage_class = django_storage.get_storage_class(
            self.django_storage_class)
        return storage_class(**self.get_options_as_dict())

    class Meta:
        app_label = 'tardis_portal'


class StorageBoxOption(models.Model):
    '''
    holds the options passed to the storage class defined in StorageBox.
    simple key: value store
    '''

    storage_box = models.ForeignKey(StorageBox, related_name='options')
    key = models.TextField()
    value = models.TextField()

    class Meta:
        app_label = 'tardis_portal'
