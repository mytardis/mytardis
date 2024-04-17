"""dataset.py

Serializer for dataset and related fields.

This module contains the Django Rest Framework serializers for the Dataset model
and related models.

Contributors:
    Chris Seal <c.seal@auckland.ac.nz>
"""

from django.conf import settings

from rest_framework import serializers

from tardis.apps.identifiers.models import DatasetID
from tardis.tardis_portal.api.serializers.instrument import InstrumentSerializer
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.parameters import DatasetParameter, DatasetParameterSet

# TODO: Integrate the datafiles into the final product. Not needed for the IDW YAML output


class DatasetIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetID
        fields = ["identifier"]


class DatasetParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetParameter
        fields = [
            "name",
            "string_value",
            "numerical_value",
            "datetime_value",
        ]


class DatasetParameterSetSerializer(serializers.ModelSerializer):
    parameters = DatasetParameterSerializer(many=True)

    class Meta:
        model = DatasetParameterSet
        fields = ["parameters"]


class DatasetSerializer(serializers.ModelSerializer):
    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APS
        and "dataset" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = DatasetIDSerializer(many=True)
    parametersets = DatasetParameterSetSerializer(many=True)
    instrument = InstrumentSerializer(many=False)

    class Meta:
        model = Dataset
        fields = [
            "description",
            "directory",
            "created_time",
            "modified_time",
            "instrument",
            "paramtersets",
        ]
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APS
            and "dataset" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            fields.append("identifiers")
