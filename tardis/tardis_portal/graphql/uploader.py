import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection

from ...apps.mydata.models.storage import Uploader as UploaderModel


class UploaderType(ModelType):
    class Meta:
        model = UploaderModel
        permissions = ['mydata.view_uploader']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class UploaderTypeFilter(FilterSet):
    class Meta:
        model = UploaderModel
        fields = {
            'name': ['exact', 'contains'],
            'uuid': ['exact', 'contains']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('name', 'name')
        )
    )


class CreateUploader(ModelCreateMutation):
    class Meta:
        model = UploaderModel
        permissions = ['mydata.add_uploader']


class UpdateUploader(ModelUpdateMutation):
    class Meta:
        model = UploaderModel
        permissions = ['mydata.change_uploader']
