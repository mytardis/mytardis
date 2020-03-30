import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection

from ...apps.mydata.models.uploader import (
    Uploader as UploaderModel,
    UploaderRegistrationRequest as UploaderRegistrationRequestModel,
    UploaderSetting as UploaderSettingModel
)

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


class UploaderRegistrationRequestType(ModelType):
    class Meta:
        model = UploaderRegistrationRequestModel
        permissions = ['mydata.view_uploaderregistrationrequest']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class UploaderRegistrationRequestTypeFilter(FilterSet):
    class Meta:
        model = UploaderRegistrationRequestModel
        fields = {
            'uploader_id': ['exact']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=()
    )


class CreateUploaderRegistrationRequest(ModelCreateMutation):
    class Meta:
        model = UploaderRegistrationRequestModel
        permissions = ['mydata.add_uploaderregistrationrequest']


class UpdateUploaderRegistrationRequest(ModelUpdateMutation):
    class Meta:
        model = UploaderRegistrationRequestModel
        permissions = ['mydata.change_uploaderregistrationrequest']


class UploaderSettingType(ModelType):
    class Meta:
        model = UploaderSettingModel
        permissions = ['mydata.view_uploadersetting']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class UploaderSettingTypeFilter(FilterSet):
    class Meta:
        model = UploaderSettingModel
        fields = {
            'uploader_id': ['exact']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('key', 'key')
        )
    )


class CreateUploaderSetting(ModelCreateMutation):
    class Meta:
        model = UploaderSettingModel
        permissions = ['mydata.add_uploadersetting']


class UpdateUploaderSetting(ModelUpdateMutation):
    class Meta:
        model = UploaderSettingModel
        permissions = ['mydata.change_uploadersetting']
