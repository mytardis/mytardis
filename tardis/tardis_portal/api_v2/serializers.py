from django.contrib.auth.models import User, Group
from rest_framework import serializers

from ..models.facility import Facility


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
