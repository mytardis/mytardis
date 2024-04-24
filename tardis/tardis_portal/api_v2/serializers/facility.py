"""facility.py

Serializer for facilities and related fields.

This module contains the Django Rest Framework serializers for the Facility model
and related models.

Contributors:
    Chris Seal <c.seal@auckland.ac.nz>
"""

from django.conf import settings

from rest_framework import serializers

from tardis.apps.identifiers.models import FacilityID
from tardis.tardis_portal.api_v2.serializers.groups import GroupSerializer
from tardis.tardis_portal.models.facility import Facility


class FacilityIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityID
        fields = ["identifier"]


class FacilitySerializer(serializers.ModelSerializer):
    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APS
        and "facility" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = FacilityIDSerializer(many=True)
    manager_group = GroupSerializer(many=True)

    class Meta:
        model = Facility
        fields = [
            "name",
            "created_time",
            "modified_time",
            "manager_group",
        ]
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APS
            and "facility" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            fields.append("identifiers")
