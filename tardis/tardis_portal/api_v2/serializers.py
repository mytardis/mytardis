from django.contrib.auth.models import User, Group
from rest_framework import serializers

from ..models.facility import Facility
from ..models.instrument import Instrument
from ..models.storage import StorageBox
from ..models.experiment import Experiment
from ..models.dataset import Dataset
from ..models.datafile import DataFile, DataFileObject


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class FacilitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Facility
        fields = ['id', 'name', 'manager_group', 'created_time', 'modified_time']


class InstrumentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Instrument
        fields = ['id', 'name', 'facility', 'created_time', 'modified_time']


class StorageBoxSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StorageBox
        fields = ['id', 'django_storage_class', 'name', 'description',
                  'master_box', 'max_size', 'status']


class ExperimentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Experiment
        fields = ['id', 'title', 'description', 'created_time', 'created_by',
                  'institution_name']


class DatasetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Dataset
        fields = ['id', 'experiments', 'description', 'directory',
                  'created_time', 'modified_time', 'immutable', 'instrument']


class DataFileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataFile
        fields = ['id', 'dataset', 'filename', 'directory', 'size',
                  'created_time', 'modification_time', 'mimetype',
                  'md5sum']


class DataFileObjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataFileObject
        fields = ['id', 'datafile', 'storage_box', 'uri', 'verified',
                  'created_time', 'last_verified_time']
