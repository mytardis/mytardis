"""experiment.py

Serializer for experiment and related fields.

This module contains the Django Rest Framework serializers for the Experiment model
and related models.

Contributors:
    Chris Seal <c.seal@auckland.ac.nz>
"""

from django.conf import settings

from rest_framework import serializers

from tardis.apps.dataclassification.models import ExperimentDataClassification
from tardis.apps.identifiers.models import ExperimentID
from tardis.apps.projects.models import Project
from tardis.tardis_portal.api_v2.serializers.project import ProjectIDSerializer
from tardis.tardis_portal.api_v2.serializers.schema import (
    ParameterNameSerializer,
    SchemaSerializer,
)
from tardis.tardis_portal.api_v2.serializers.user import UserSerializer
from tardis.tardis_portal.auth.decorators import (
    get_accessible_projects_for_experiment,
    has_sensitive_access,
)
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.parameters import (
    ExperimentParameter,
    ExperimentParameterSet,
)


class ExperimentParameterSerializer(serializers.ModelSerializer):
    name = ParameterNameSerializer()

    class Meta:
        model = ExperimentParameter
        fields = [
            "name",
            "string_value",
            "numerical_value",
            "datetime_value",
        ]


class ExperimentParameterSetSerializer(serializers.ModelSerializer):
    parameters = serializers.SerializerMethodField("get_safe_parameters")
    schema = SchemaSerializer()

    class Meta:
        model = ExperimentParameterSet
        fields = ["schema", "parameters"]

    def get_safe_parameters(self, parameterset_obj):
        experiment = parameterset_obj.experiment
        queryset = ExperimentParameter.objects.filter(parameterset=parameterset_obj)
        parameters = ExperimentParameterSerializer(
            queryset, many=True, context=self.context
        ).data
        if has_sensitive_access(self.context["request"], experiment.pk, "experiment"):
            return parameters
        return [item for item in parameters if item.name.sensitive is not True]


class ExperimentIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentID
        fields = ["identifier"]


class ExperimentDataclassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentDataClassification
        fields = ["classification"]


class ExperimentProjectSerializer(serializers.ModelSerializer):
    """A subset Project serializer to prevent infinite recursion"""

    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "project" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = ProjectIDSerializer(many=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
        ]
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APPS
            and "projects" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            fields.append("identifiers")


class ExperimentSerializer(serializers.ModelSerializer):
    experimentparameterset_set = ExperimentParameterSetSerializer(many=True)
    created_by = UserSerializer(many=False)
    user_acls = serializers.SerializerMethodField("get_user_acls")
    group_acls = serializers.SerializerMethodField("get_group_acls")
    projects = serializers.SerializerMethodField("get_projects")

    # datasets = serializers.SerializerMethodField("get_datasets")

    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "experiment" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = ExperimentIDSerializer(many=True)
    if "tardis.apps.dataclassification" in settings.INSTALLED_APPS:
        data_classification = ExperimentDataclassificationSerializer()

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
            "experimentparameterset_set",
            "url",
            "user_acls",
            "group_acls",
        ]
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APPS
            and "experiment" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            fields.append("identifiers")
        if "tardis.apps.dataclassification" in settings.INSTALLED_APPS:
            fields.append("data_classification")
        if "tardis.apps.projects" in settings.INSTALLED_APPS:
            fields.append("projects")

    def get_user_acls(self, obj):  # TODO wrap in tests for micro/macro ACLS
        acls = obj.experimentacl_set.select_related("user").filter(user__isnull=False)
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
        acls = obj.experimentacl_set.select_related("group").filter(group__isnull=False)
        return [
            {
                "group": acl.get_related_object().name,
                "can_download": acl.canDownload,
                "see_sensitive": acl.canSensitive,
                "is_owner": acl.isOwner,
            }
            for acl in acls
        ]

    def get_projects(self, obj):
        user = self.context["request"].user
        exp_id = obj.id
        q1 = Project.safe.all(user=user)
        q2 = Project.objects.filter(experiments__id=obj.id)
        queryset = get_accessible_projects_for_experiment(
            self.context["request"], obj.id
        )
        return ExperimentProjectSerializer(
            queryset, many=True, context=self.context
        ).data
