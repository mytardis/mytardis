import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection

from ..models.storage import StorageBox as StorageBoxModel


class StorageBoxType(ModelType):
    class Meta:
        model = StorageBoxModel
        permissions = ['tardis_portal.view_storagebox']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class StorageBoxTypeFilter(FilterSet):
    class Meta:
        model = StorageBoxModel
        fields = {
            'name': ['exact', 'contains']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('name', 'name')
        )
    )


class CreateStorageBox(ModelCreateMutation):
    class Meta:
        model = StorageBoxModel
        permissions = ['tardis_portal.add_storagebox']


class UpdateStorageBox(ModelUpdateMutation):
    class Meta:
        model = StorageBoxModel
        permissions = ['tardis_portal.change_storagebox']
