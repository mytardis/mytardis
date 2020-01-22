import graphene
from graphene import Node
from graphene_django.types import DjangoObjectType

from django.contrib.auth.models import Group as GroupModel

from .utils import ExtendedConnection


class GroupType(DjangoObjectType):
    class Meta:
        model = GroupModel
        filter_fields = {
            'id': ['exact']
        }
        interfaces = (Node,)
        connection_class = ExtendedConnection

    pk = graphene.Field(type=graphene.Int, source='pk')
