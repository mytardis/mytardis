import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection

from ..models.datafile import DataFileObject as DataFileObjectModel


class DataFileObjectType(ModelType):
    class Meta:
        model = DataFileObjectModel
        permissions = ['tardis_portal.view_datafileobject']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class DataFileObjectTypeFilter(FilterSet):
    class Meta:
        model = DataFileObjectModel
        fields = {
            'verified': ['exact'],
            'created_time': ['lte', 'gte']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('verified', 'verified'),
            ('created_time', 'created_time')
        )
    )


class CreateDataFileObject(ModelCreateMutation):
    class Meta:
        model = DataFileObjectModel
        permissions = ['tardis_portal.add_datafileobject']


class UpdateDataFileObject(ModelUpdateMutation):
    class Meta:
        model = DataFileObjectModel
        permissions = ['tardis_portal.change_datafileobject']
