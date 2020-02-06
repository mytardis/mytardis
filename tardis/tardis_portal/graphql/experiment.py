import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

import itertools
from django.db import (
    models,
    transaction,
)

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection

from ..models.experiment import Experiment as ExperimentModel
from ..models.access_control import ObjectACL


class ExperimentType(ModelType):
    class Meta:
        model = ExperimentModel
        permissions = ['tardis_portal.view_experiment']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class ExperimentTypeFilter(FilterSet):
    class Meta:
        model = ExperimentModel
        fields = {
            'title': ['exact', 'contains'],
            'created_time': ['lte', 'gte']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('title', 'name'),
            ('created_time', 'createdTime')
        )
    )


class CreateExperiment(ModelCreateMutation):
    class Meta:
        model = ExperimentModel
        permissions = ['tardis_portal.add_experiment']
        required_fields = ['title', 'institution_name', 'description']
        exclude_fields = ['created_by', 'created_time', 'update_time']

    @classmethod
    def clean_instance(cls, instance, clean_input):
        return instance

    @classmethod
    def before_save(cls, info, instance, cleaned_input=None):
        user = info.context.user
        instance.created_by = user
        try:
            instance.full_clean()
        except Exception as e:
            raise e

    @classmethod
    def after_save(cls, info, instance, cleaned_input=None):
        user = info.context.user
        acl = ObjectACL(
            content_object=instance,
            pluginId="django_user",
            entityId=user.id,
            isOwner=True,
            canRead=True,
            canWrite=True,
            canDelete=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED
        )
        acl.save()


class UpdateExperiment(ModelUpdateMutation):
    class Meta:
        model = ExperimentModel
        permissions = ['tardis_portal.change_experiment']
        exclude_fields = ['created_by', 'created_time', 'update_time']
