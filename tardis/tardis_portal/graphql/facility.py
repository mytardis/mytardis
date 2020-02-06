import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter
from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection
from ..models.facility import Facility as FacilityModel


class FacilityType(ModelType):
    class Meta:
        model = FacilityModel
        permissions = ['tardis_portal.view_facility']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class FacilityTypeFilter(FilterSet):
    class Meta:
        model = FacilityModel
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


class CreateFacility(ModelCreateMutation):
    class Meta:
        model = FacilityModel
        permissions = ['tardis_portal.add_facility']


class UpdateFacility(ModelUpdateMutation):
    class Meta:
        model = FacilityModel
        permissions = ['tardis_portal.change_facility']
