import graphene
from graphene import Node
from graphene_django.types import DjangoObjectType
# from django_filters import FilterSet, OrderingFilter
# from graphql_jwt.decorators import login_required

from .utils import ExtendedConnection
from ..models.facility import Facility as FacilityModel


class FacilityType(DjangoObjectType):
    class Meta:
        model = FacilityModel
        filter_fields = {
            'id': ['exact']
        }
        interfaces = (Node,)
        connection_class = ExtendedConnection

    pk = graphene.Field(type=graphene.Int, source='pk')
