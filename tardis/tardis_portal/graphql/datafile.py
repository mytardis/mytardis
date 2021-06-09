import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from django.conf import settings

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection

from ..models.datafile import (
    DataFile as DataFileModel,
    DataFileObject as DataFileObjectModel,
    compute_checksums
)


class DataFileType(ModelType):
    class Meta:
        model = DataFileModel
        permissions = ['tardis_portal.view_datafile']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class DataFileTypeFilter(FilterSet):
    class Meta:
        model = DataFileModel
        fields = {
            'filename': ['exact', 'contains'],
            'directory': ['exact', 'contains'],
            'created_time': ['lte', 'gte']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('filename', 'filename'),
            ('directory', 'directory'),
            ('created_time', 'created_time')
        )
    )


class CreateDataFile(ModelCreateMutation):
    class Meta:
        model = DataFileModel
        permissions = ['tardis_portal.add_datafile']


class UpdateDataFile(ModelUpdateMutation):
    class Meta:
        model = DataFileModel
        permissions = ['tardis_portal.change_datafile']


class UploadDataFile(ModelCreateMutation):
    class Meta:
        model = DataFileModel
        permissions = ['tardis_portal.add_datafile']

    @classmethod
    def clean_input(cls, info, instance, data):
        if info.context.FILES and 'file' in info.context.FILES:
            newfile = info.context.FILES['file']
            data['filename'] = newfile.name
            data['size'] = newfile.size
            compute_md5 = getattr(settings, 'COMPUTE_MD5', True)
            compute_sha512 = getattr(settings, 'COMPUTE_SHA512', True)
            checksums = compute_checksums(newfile, close_file=False)
            if compute_md5:
                data['md5sum'] = checksums['md5sum']
            if compute_sha512:
                data['sha512sum'] = checksums['sha512sum']
        return super().clean_input(info, instance, data)

    @classmethod
    def after_save(cls, info, instance, cleaned_input=None):
        dfo = DataFileObjectModel(
            datafile=instance,
            storage_box=instance.get_default_storage_box()
        )
        dfo.file_object = info.context.FILES['file']
