import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection
from ..models.instrument import Instrument as InstrumentModel


class InstrumentType(ModelType):
    class Meta:
        model = InstrumentModel
        permissions = ['tardis_portal.view_instrument']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class InstrumentTypeFilter(FilterSet):
    class Meta:
        model = InstrumentModel
        fields = {
            'name': ['exact', 'contains'],
            'created_time': ['lte', 'gte']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('name', 'name'),
            ('created_time', 'created_time')
        )
    )


class CreateInstrument(ModelCreateMutation):
    class Meta:
        model = InstrumentModel
        permissions = ['tardis_portal.add_instrument']


class UpdateInstrument(ModelUpdateMutation):
    class Meta:
        model = InstrumentModel
        permissions = ['tardis_portal.change_instrument']
