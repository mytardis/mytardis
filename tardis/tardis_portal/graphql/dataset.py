import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection

from ..models.dataset import Dataset as DatasetModel


class DatasetType(ModelType):
    class Meta:
        model = DatasetModel
        permissions = ['tardis_portal.view_dataset']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class DatasetTypeFilter(FilterSet):
    class Meta:
        model = DatasetModel
        fields = {
            'description': ['exact', 'contains'],
            'created_time': ['lte', 'gte']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('description', 'description'),
            ('created_time', 'created_time')
        )
    )


class CreateDataset(ModelCreateMutation):
    class Meta:
        model = DatasetModel
        permissions = ['tardis_portal.add_dataset']


class UpdateDataset(ModelUpdateMutation):
    class Meta:
        model = DatasetModel
        permissions = ['tardis_portal.change_dataset']
