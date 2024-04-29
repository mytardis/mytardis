"""instrument.py

Serializer for instrument and related fields.

This module contains the Django Rest Framework serializers for the Instrument model
and related models.

Contributors:
    Chris Seal <c.seal@auckland.ac.nz>
"""

from django.conf import settings

from rest_framework import serializers

from tardis.apps.identifiers.models import InstrumentID
from tardis.tardis_portal.api_v2.serializers.facility import FacilitySerializer
from tardis.tardis_portal.api_v2.serializers.schema import ParameterNameSerializer
from tardis.tardis_portal.models.instrument import Instrument
from tardis.tardis_portal.models.parameters import (
    InstrumentParameter,
    InstrumentParameterSet,
)


class InstrumentParameterSerializer(serializers.ModelSerializer):
    name = ParameterNameSerializer()

    class Meta:
        model = InstrumentParameter
        fields = [
            "name",
            "string_value",
            "numerical_value",
            "datetime_value",
        ]


class InstrumentParameterSetSerializer(serializers.ModelSerializer):
    parameters = InstrumentParameterSerializer(many=True)

    class Meta:
        model = InstrumentParameterSet
        fields = ["parameters"]


class InstrumentIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstrumentID
        fields = ["identifier"]


class InstrumentSerializer(serializers.ModelSerializer):
    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "instrument" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = InstrumentIDSerializer(many=True)
    instrumentparameterset_set = InstrumentParameterSetSerializer(many=True)
    facility = FacilitySerializer(many=False)

    class Meta:
        model = Instrument
        fields = [
            "name",
            "created_time",
            "modified_time",
            "facility",
            "instrumentparameterset_set",
        ]
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APPS
            and "instrument" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            fields.append("identifiers")
