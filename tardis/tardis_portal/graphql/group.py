import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from django.contrib.auth.models import Group as GroupModel

from .utils import ExtendedConnection


class GroupType(ModelType):
    class Meta:
        model = GroupModel
        permissions = ['auth.view_group']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class GroupTypeFilter(FilterSet):
    class Meta:
        model = GroupModel
        fields = {
            'name': ['exact', 'contains']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('name', 'name')
        )
    )


class CreateGroup(ModelCreateMutation):
    class Meta:
        model = GroupModel
        permissions = ['auth.add_group']


class UpdateGroup(ModelUpdateMutation):
    class Meta:
        model = GroupModel
        permissions = ['auth.change_group']
