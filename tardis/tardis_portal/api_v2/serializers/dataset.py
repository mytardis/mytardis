"""dataset.py

Serializer for dataset and related fields.

This module contains the Django Rest Framework serializers for the Dataset model
and related models.

Contributors:
    Chris Seal <c.seal@auckland.ac.nz>
"""

from django.conf import settings

from rest_framework import serializers

from tardis.apps.dataclassification.models import DatasetDataClassification
from tardis.apps.identifiers.models import DatasetID
from tardis.tardis_portal.api_v2.serializers.experiment import ExperimentIDSerializer
from tardis.tardis_portal.api_v2.serializers.instrument import InstrumentSerializer
from tardis.tardis_portal.api_v2.serializers.schema import (
    ParameterNameSerializer,
    SchemaSerializer,
)
from tardis.tardis_portal.auth.decorators import has_sensitive_access
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.parameters import DatasetParameter, DatasetParameterSet

# TODO: Integrate the datafiles into the final product. Not needed for the IDW YAML output


class DatasetParameterSerializer(serializers.ModelSerializer):
    name = ParameterNameSerializer()

    class Meta:
        model = DatasetParameter
        fields = [
            "name",
            "string_value",
            "numerical_value",
            "datetime_value",
        ]


class DatasetParameterSetSerializer(serializers.ModelSerializer):
    parameters = serializers.SerializerMethodField("get_safe_parameters")
    schema = SchemaSerializer()

    class Meta:
        model = DatasetParameterSet
        fields = ["schema", "parameters"]

    def get_safe_parameters(self, parameterset_obj):
        dataset = parameterset_obj.dataset
        queryset = DatasetParameter.objects.filter(parameterset=parameterset_obj)
        parameters = DatasetParameterSerializer(
            queryset, many=True, context=self.context
        ).data
        if has_sensitive_access(self.context["request"], dataset.pk, "dataset"):
            return parameters
        return [item for item in parameters if item.name.sensitive is not True]


class DatasetIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetID
        fields = ["identifier"]


class DatasetDataclassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetDataClassification
        fields = ["classification"]


class DatasetExperimentSerializer(serializers.ModelSerializer):
    """A subset Dataset serializer to prevent infinite recursion"""

    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "project" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = ExperimentIDSerializer(many=True)

    class Meta:
        model = Experiment
        fields = [
            "id",
            "title",
        ]
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APPS
            and "experiment" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            fields.append("identifiers")


# TODO: Add a DatasetDatafileSerializer to provide more useful data than just the id
class DatasetSerializer(serializers.ModelSerializer):

    datasetparameterset_set = DatasetParameterSetSerializer(many=True)
    instrument = InstrumentSerializer(many=False)
    user_acls = serializers.SerializerMethodField("get_user_acls")
    group_acls = serializers.SerializerMethodField("get_group_acls")
    experiments = serializers.SerializerMethodField("get_experiments")

    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "dataset" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = DatasetIDSerializer(many=True)
    if "tardis.apps.dataclassification" in settings.INSTALLED_APPS:
        data_classification = DatasetDataclassificationSerializer()

    class Meta:
        model = Dataset
        fields = [
            "description",
            "directory",
            "created_time",
            "modified_time",
            "instrument",
            "datasetparamterset_set",
            "experiments",
            "user_acls",
            "group_acls",
        ]
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APPS
            and "dataset" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            fields.append("identifiers")
        if "tardis.apps.dataclassification" in settings.INSTALLED_APPS:
            fields.append("data_classification")

    def get_user_acls(self, obj):  # TODO wrap in tests for micro/macro ACLS
        acls = obj.datasetacl_set.select_related("user").filter(user__isnull=False)
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
        acls = obj.datasetacl_set.select_related("group").filter(group__isnull=False)
        return [
            {
                "group": acl.get_related_object().name,
                "can_download": acl.canDownload,
                "see_sensitive": acl.canSensitive,
                "is_owner": acl.isOwner,
            }
            for acl in acls
        ]

    def get_experiments(self, obj):
        queryset = Experiment.safe.all(user=self.context["request"].user).filter(
            datasets__id=obj.id
        )
        return DatasetExperimentSerializer(
            queryset, many=True, context=self.context
        ).data
