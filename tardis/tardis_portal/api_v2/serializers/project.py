"""project.py

Serializer for project and related fields.

This module contains the Django Rest Framework serializers for the Project model
and related models.

Contributors:
    Chris Seal <c.seal@auckland.ac.nz>
"""


import logging

from django.conf import settings

from rest_framework import serializers

from tardis.apps.dataclassification.models import ProjectDataClassification
from tardis.apps.identifiers.models import InstitutionID, ProjectID
from tardis.apps.projects.models import (
    Institution,
    Project,
    ProjectParameter,
    ProjectParameterSet,
)
from tardis.tardis_portal.api_v2.serializers.schema import (
    ParameterNameSerializer,
    SchemaSerializer,
)

# from tardis.tardis_portal.api.serializers.experiment import ExperimentSerializer
from tardis.tardis_portal.api_v2.serializers.user import UserSerializer
from tardis.tardis_portal.auth.decorators import has_sensitive_access

# from tardis.tardis_portal.models.experiment import Experiment
logger = logging.getLogger("__name__")


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
    name = ParameterNameSerializer()

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
    schema = SchemaSerializer()

    class Meta:
        model = ProjectParameterSet
        fields = ["schema", "parameters"]

    def get_safe_parameters(self, parameterset_obj):
        logger.debug(self.context)
        project = parameterset_obj.project
        queryset = ProjectParameter.objects.filter(parameterset=parameterset_obj)
        parameters = ProjectParameterSerializer(
            queryset, many=True, context=self.context
        ).data
        if has_sensitive_access(self.context["request"], project.pk, "project"):
            return parameters
        return [item for item in parameters if item.name.sensitive is not True]


class ProjectIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectID
        fields = ["identifier"]


class ProjectDataclassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDataClassification
        fields = ["classification"]


class ProjectSerializer(serializers.ModelSerializer):
    projectparameterset_set = ProjectParameterSetSerializer(many=True)
    principal_investigator = UserSerializer(many=False)
    institution = InstitutionSerializer(many=True)
    created_by = UserSerializer(many=False)
    user_acls = serializers.SerializerMethodField("get_user_acls")
    group_acls = serializers.SerializerMethodField("get_group_acls")

    # experiments = serializers.SerializerMethodField("get_experiments")

    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "project" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = ProjectIDSerializer(many=True)
    if "tardis.apps.dataclassification" in settings.INSTALLED_APPS:
        data_classification = ProjectDataclassificationSerializer()

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
            "projectparameterset_set",
            "user_acls",
            "group_acls",
        ]
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APPS
            and "project" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            fields.append("identifiers")
        if "tardis.apps.dataclassification" in settings.INSTALLED_APPS:
            fields.append("data_classification")

    def get_user_acls(self, obj):  # TODO wrap in tests for micro/macro ACLS
        acls = obj.projectacl_set.select_related("user").filter(user__isnull=False)
        return [
            {
                "user": acl.get_related_object().username,
                "can_download": acl.canDownload,
                "see_sensitive": acl.canSensitive,
                "is_owner": acl.isOwner,
            }
            for acl in acls
        ]

    def get_group_acls(self, obj):  # TODO wrap in tests for micro/macro ACLS
        acls = obj.projectacl_set.select_related("group").filter(group__isnull=False)
        return [
            {
                "group": acl.get_related_object().name,
                "can_download": acl.canDownload,
                "see_sensitive": acl.canSensitive,
                "is_owner": acl.isOwner,
            }
            for acl in acls
        ]

    # def get_experiments(self):
    #    if request := self.context.get("request", None):
    #        queryset = Experiment.safe.all(user=request.user)
    #        return ExperimentSerializer(queryset, many=True, context=self.context).data
    #    return None
