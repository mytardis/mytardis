from django.contrib.auth.models import User, Group
from rest_framework import serializers

from ..models.facility import Facility
from ..models.instrument import Instrument
from ..models.storage import StorageBox, StorageBoxOption, StorageBoxAttribute
from ..models.experiment import Experiment
from ..models.dataset import Dataset
from ..models.datafile import DataFile, DataFileObject
from ..models.parameters import (Schema, ParameterName, Parameter,
                                 ExperimentParameterSet, ExperimentParameter,
                                 DatasetParameterSet, DatasetParameter,
                                 DatafileParameterSet, DatafileParameter)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ['id', 'name', 'manager_group', 'created_time', 'modified_time']


class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = ['id', 'name', 'facility', 'created_time', 'modified_time']


class StorageBoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageBox
        fields = ['id', 'django_storage_class', 'name', 'description',
                  'master_box', 'max_size', 'status', 'options', 'attributes']


class StorageBoxOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageBoxOption
        fields = ['id', 'storage_box', 'key', 'value']


class StorageBoxAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageBoxAttribute
        fields = ['id', 'storage_box', 'key', 'value']


class ExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experiment
        fields = ['id', 'title', 'description', 'created_time', 'created_by',
                  'institution_name']


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['id', 'experiments', 'description', 'directory',
                  'created_time', 'modified_time', 'immutable', 'instrument']


class DataFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataFile
        fields = ['id', 'dataset', 'filename', 'directory', 'size',
                  'created_time', 'modification_time', 'mimetype',
                  'md5sum']


class DataFileObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataFileObject
        fields = ['id', 'datafile', 'storage_box', 'uri', 'verified',
                  'created_time', 'last_verified_time']


class SchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schema
        fields = ['id', 'namespace', 'name', 'type', 'subtype', 'immutable',
                  'hidden']


class ParameterNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParameterName
        fields = ['id', 'schema', 'name', 'full_name', 'units', 'data_type',
                  'immutable', 'comparison_type', 'is_searchable', 'choices',
                  'order']


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = ['id', 'parameterset', 'name', 'string_value',
                  'numerical_value', 'datetime_value']


class ExperimentParameterSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentParameterSet
        fields = ['id', 'experiment', 'schema']


class ExperimentParameterSerializer(ParameterSerializer):
    class Meta(ParameterSerializer.Meta):
        model = ExperimentParameter


class DatasetParameterSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetParameterSet
        fields = ['id', 'dataset', 'schema']


class DatasetParameterSerializer(ParameterSerializer):
    class Meta(ParameterSerializer.Meta):
        model = DatasetParameter


class DatafileParameterSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatafileParameterSet
        fields = ['id', 'datafile', 'schema']


class DatafileParameterSerializer(ParameterSerializer):
    class Meta(ParameterSerializer.Meta):
        model = DatafileParameter
