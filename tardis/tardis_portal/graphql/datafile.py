import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection

from ..models.datafile import DataFile as DataFileModel


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
            # 'description': ['exact', 'contains'],
            'created_time': ['lte', 'gte']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            # ('description', 'description'),
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
