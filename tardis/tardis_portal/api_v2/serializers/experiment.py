"""experiment.py

Serializer for experiment and related fields.

This module contains the Django Rest Framework serializers for the Experiment model
and related models.

Contributors:
    Chris Seal <c.seal@auckland.ac.nz>
"""

from django.conf import settings

from rest_framework import serializers

from tardis.apps.identifiers.models import ExperimentID
from tardis.tardis_portal.api.serializers.dataset import DatasetSerializer
from tardis.tardis_portal.api.serializers.user import UserSerializer
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.parameters import (
    ExperimentParameter,
    ExperimentParameterSet,
)


class ExperimentIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentID
        fields = ["identifier"]


class ExperimentParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentParameter
        fields = [
            "name",
            "string_value",
            "numerical_value",
            "datetime_value",
        ]


class ExperimentParameterSetSerializer(serializers.ModelSerializer):
    parameters = ExperimentParameterSerializer(many=True)

    class Meta:
        model = ExperimentParameterSet
        fields = ["parameters"]


class ExperimentSerializer(serializers.HyperlinkedModelSerializer):
    parametersets = ExperimentParameterSetSerializer(many=True)
    created_by = UserSerializer(many=True)

    # datasets = serializers.SerializerMethodField("get_datasets")

    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APS
        and "experiment" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = ExperimentIDSerializer(many=True)

    class Meta:
        model = Experiment
        fields = [
            "title",
            "description",
            "start_time",
            "end_time",
            "created_time",
            "update_time",
            "created_by",
            "datasets",
            "parametersets",
            "url",
        ]
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APS
            and "experiment" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            fields.append("identifiers")
