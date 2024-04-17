"""facility.py

Serializer for facilities and related fields.

This module contains the Django Rest Framework serializers for the Facility model
and related models.

Contributors:
    Chris Seal <c.seal@auckland.ac.nz>
"""

from django.conf import settings
from django.contrib.auth.models import User

from rest_framework import serializers

from tardis.apps.identifiers.models import UserPID


class UserIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPID
        fields = ["identifier"]


class UserSerializer(serializers.ModelSerializer):
    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "user" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = UserIDSerializer(many=True)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
        ]
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APPS
            and "user" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            fields.append("identifiers")
