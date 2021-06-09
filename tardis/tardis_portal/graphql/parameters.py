import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection

from ..models.parameters import (
    Schema as SchemaModel,
    ParameterName as ParameterNameModel,
    ExperimentParameterSet as ExperimentParameterSetModel,
    ExperimentParameter as ExperimentParameterModel,
    DatasetParameterSet as DatasetParameterSetModel,
    DatasetParameter as DatasetParameterModel,
    DatafileParameterSet as DatafileParameterSetModel,
    DatafileParameter as DatafileParameterModel
)


class TardisSchemaType(ModelType):
    class Meta:
        model = SchemaModel
        permissions = ['tardis_portal.view_schema']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class TardisSchemaTypeFilter(FilterSet):
    class Meta:
        model = SchemaModel
        fields = {
            'name': ['exact', 'contains'],
            'namespace': ['exact', 'contains']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('name', 'name'),
            # ('created_time', 'created_time')
        )
    )


class CreateSchema(ModelCreateMutation):
    class Meta:
        model = SchemaModel
        permissions = ['tardis_portal.add_schema']


class UpdateSchema(ModelUpdateMutation):
    class Meta:
        model = SchemaModel
        permissions = ['tardis_portal.change_schema']


class ParameterNameType(ModelType):
    class Meta:
        model = ParameterNameModel
        permissions = ['tardis_portal.view_parametername']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class ParameterNameTypeFilter(FilterSet):
    class Meta:
        model = ParameterNameModel
        fields = {
            'name': ['exact', 'contains'],
            'schema': ['exact']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('name', 'name'),
            ('order', 'order')
        )
    )


class CreateParameterName(ModelCreateMutation):
    class Meta:
        model = ParameterNameModel
        permissions = ['tardis_portal.add_parametername']


class UpdateParameterName(ModelUpdateMutation):
    class Meta:
        model = ParameterNameModel
        permissions = ['tardis_portal.change_parametername']


class ExperimentParameterSetType(ModelType):
    class Meta:
        model = ExperimentParameterSetModel
        permissions = ['tardis_portal.view_experimentparameterset']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class ExperimentParameterSetTypeFilter(FilterSet):
    class Meta:
        model = ExperimentParameterSetModel
        fields = {}

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=()
    )


class CreateExperimentParameterSet(ModelCreateMutation):
    class Meta:
        model = ExperimentParameterSetModel
        permissions = ['tardis_portal.add_experimentparameterset']


class UpdateExperimentParameterSet(ModelUpdateMutation):
    class Meta:
        model = ExperimentParameterSetModel
        permissions = ['tardis_portal.change_experimentparameterset']


class ExperimentParameterType(ModelType):
    class Meta:
        model = ExperimentParameterModel
        permissions = ['tardis_portal.view_experimentparameter']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class ExperimentParameterTypeFilter(FilterSet):
    class Meta:
        model = ExperimentParameterModel
        fields = {}

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=()
    )


class CreateExperimentParameter(ModelCreateMutation):
    class Meta:
        model = ExperimentParameterModel
        permissions = ['tardis_portal.add_experimentparameter']


class UpdateExperimentParameter(ModelUpdateMutation):
    class Meta:
        model = ExperimentParameterModel
        permissions = ['tardis_portal.change_experimentparameter']


class DatasetParameterSetType(ModelType):
    class Meta:
        model = DatasetParameterSetModel
        permissions = ['tardis_portal.view_datasetparameterset']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class DatasetParameterSetTypeFilter(FilterSet):
    class Meta:
        model = DatasetParameterSetModel
        fields = {}

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=()
    )


class CreateDatasetParameterSet(ModelCreateMutation):
    class Meta:
        model = DatasetParameterSetModel
        permissions = ['tardis_portal.add_datasetparameterset']


class UpdateDatasetParameterSet(ModelUpdateMutation):
    class Meta:
        model = DatasetParameterSetModel
        permissions = ['tardis_portal.change_datasetparameterset']


class DatasetParameterType(ModelType):
    class Meta:
        model = DatasetParameterModel
        permissions = ['tardis_portal.view_datasetparameter']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class DatasetParameterTypeFilter(FilterSet):
    class Meta:
        model = DatasetParameterModel
        fields = {}

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=()
    )


class CreateDatasetParameter(ModelCreateMutation):
    class Meta:
        model = DatasetParameterModel
        permissions = ['tardis_portal.add_datasetparameter']


class UpdateDatasetParameter(ModelUpdateMutation):
    class Meta:
        model = DatasetParameterModel
        permissions = ['tardis_portal.change_datasetparameter']


class DatafileParameterSetType(ModelType):
    class Meta:
        model = DatafileParameterSetModel
        permissions = ['tardis_portal.view_datafileparameterset']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class DatafileParameterSetTypeFilter(FilterSet):
    class Meta:
        model = DatafileParameterSetModel
        fields = {}

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=()
    )


class CreateDatafileParameterSet(ModelCreateMutation):
    class Meta:
        model = DatafileParameterSetModel
        permissions = ['tardis_portal.add_datafileparameterset']


class UpdateDatafileParameterSet(ModelUpdateMutation):
    class Meta:
        model = DatafileParameterSetModel
        permissions = ['tardis_portal.change_datafileparameterset']


class DatafileParameterType(ModelType):
    class Meta:
        model = DatafileParameterModel
        permissions = ['tardis_portal.view_datafileparameter']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class DatafileParameterTypeFilter(FilterSet):
    class Meta:
        model = DatafileParameterModel
        fields = {}

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=()
    )


class CreateDatafileParameter(ModelCreateMutation):
    class Meta:
        model = DatafileParameterModel
        permissions = ['tardis_portal.add_datafileparameter']


class UpdateDatafileParameter(ModelUpdateMutation):
    class Meta:
        model = DatafileParameterModel
        permissions = ['tardis_portal.change_datafileparameter']
