from rest_framework import serializers

from tardis.tardis_portal.models.parameters import ParameterName, Schema


class ParameterNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParameterName
        fields = ["name", "sensitive"]


class SchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schema
        fields = ["namespace", "name", "type"]
