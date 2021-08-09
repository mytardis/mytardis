import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection

from ..models.storage import StorageBoxOption as StorageBoxOptionModel


class StorageBoxOptionType(ModelType):
    class Meta:
        model = StorageBoxOptionModel
        permissions = ['tardis_portal.view_storageboxoption']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class StorageBoxOptionTypeFilter(FilterSet):
    class Meta:
        model = StorageBoxOptionModel
        fields = {
            'id': ['exact'],
            'key': ['exact', 'contains'],
            'value': ['exact', 'contains']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('key', 'key'),
            ('value', 'value')
        )
    )


class CreateStorageBoxOption(ModelCreateMutation):
    class Meta:
        model = StorageBoxOptionModel
        permissions = ['tardis_portal.add_storageboxoption']


class UpdateStorageBoxOption(ModelUpdateMutation):
    class Meta:
        model = StorageBoxOptionModel
        permissions = ['tardis_portal.change_storageboxoption']
