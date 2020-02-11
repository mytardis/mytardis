import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection

from ..models.storage import StorageBoxAttribute as StorageBoxAttributeModel


class StorageBoxAttributeType(ModelType):
    class Meta:
        model = StorageBoxAttributeModel
        permissions = ['tardis_portal.view_storageboxattribute']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class StorageBoxAttributeTypeFilter(FilterSet):
    class Meta:
        model = StorageBoxAttributeModel
        fields = {
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


class CreateStorageBoxAttribute(ModelCreateMutation):
    class Meta:
        model = StorageBoxAttributeModel
        permissions = ['tardis_portal.add_storageboxattribute']


class UpdateStorageBoxAttribute(ModelUpdateMutation):
    class Meta:
        model = StorageBoxAttributeModel
        permissions = ['tardis_portal.change_storageboxattribute']
