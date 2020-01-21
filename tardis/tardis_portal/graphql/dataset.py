import graphene
from graphene import Node
from graphene_django.types import DjangoObjectType
# from django_filters import FilterSet, OrderingFilter
# from graphql_jwt.decorators import login_required

from .utils import ExtendedConnection
from ..models.dataset import Dataset as DatasetModel


class DatasetType(DjangoObjectType):
    class Meta:
        model = DatasetModel
        filter_fields = {
            'id': ['exact']
        }
        interfaces = (Node,)
        connection_class = ExtendedConnection

    pk = graphene.Field(type=graphene.Int, source='pk')
