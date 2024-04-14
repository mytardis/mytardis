"""project.py

Serializer for project and related fields.

This module contains the Django Rest Framework serializers for the Project model
and related models.

Contributors:
    Chris Seal <c.seal@auckland.ac.nz>
"""


from django.conf import settings

from rest_framework import serializers

from tardis.apps.identifiers.models import InstitutionID, ProjectID
from tardis.apps.projects.models import (
    Institution,
    Project,
    ProjectParameter,
    ProjectParameterSet,
)

# from tardis.tardis_portal.api.serializers.experiment import ExperimentSerializer
from tardis.tardis_portal.api.serializers.user import UserSerializer
from tardis.tardis_portal.auth.decorators import has_sensitive_access

# from tardis.tardis_portal.models.experiment import Experiment


class InstitutionIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionID
        fields = ["identifier"]


class InstitutionSerializer(serializers.ModelSerializer):

    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "institution" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = InstitutionIDSerializer(many=True)

    class Meta:
        model = Institution
        fields = [
            "name",
            "url",
            "institution_type",
            "date_established",
            "address",
            "aliases",
            "status",
            "country",
        ]
        if "tardis.apps.identifiers" in settings.INSTALLED_APPS:
            fields.append("identifiers")


class ProjectParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectParameter
        fields = [
            "name",
            "string_value",
            "numerical_value",
            "datetime_value",
        ]


class ProjectParameterSetSerializer(serializers.ModelSerializer):
    # parameters = ProjectParameterSerializer(many=True)
    parameters = serializers.SerializerMethodField("get_safe_parameters")

    class Meta:
        model = ProjectParameterSet
        fields = ["paramters"]

    def get_safe_parameters(self, parameterset_obj):
        project = parameterset_obj.project
        queryset = ProjectParameter.objects.filter(parameterset=parameterset_obj)
        parameters = ProjectParameterSerializer(
            queryset, many=True, context=self.context
        ).data
        if has_sensitive_access(self.context.request, project.pk, "project"):
            return parameters
        return [item for item in parameters if item.name.sensitive is not True]


class ProjectIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectID
        fields = ["identifier"]


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    paramtersets = ProjectParameterSetSerializer(many=True)
    principal_investigator = UserSerializer(many=False)
    institution = InstitutionSerializer(many=True)
    created_by = UserSerializer(many=True)

    # experiments = serializers.SerializerMethodField("get_experiments")

    if (
        "tardis.apps.identifers" in settings.INSTALLED_APPS
        and "project" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = ProjectIDSerializer(many=True)

    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "locked",
            "principal_investigator",
            "experiments",
            "institution",
            "embargo_until",
            "start_time",
            "end_time",
            "created_by",
            "url",
        ]
        if (
            "tardis.apps.identifers" in settings.INSTALLED_APPS
            and "project" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            fields.append("identifiers")

    # def get_experiments(self):
    #    if request := self.context.get("request", None):
    #        queryset = Experiment.safe.all(user=request.user)
    #        return ExperimentSerializer(queryset, many=True, context=self.context).data
    #    return None
