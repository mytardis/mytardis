import graphene
from graphene import Node
from graphene_django.types import DjangoObjectType
# from django_filters import FilterSet, OrderingFilter
from graphql_jwt.decorators import login_required

from .utils import ExtendedConnection
from ..models.experiment import Experiment as ExperimentModel
from ..models.access_control import ObjectACL


class ExperimentType(DjangoObjectType):
    class Meta:
        model = ExperimentModel
        filter_fields = {
            'id': ['exact']
        }
        interfaces = (Node,)
        connection_class = ExtendedConnection

    pk = graphene.Field(type=graphene.Int, source='pk')

    # order_by = OrderingFilter(
    #     fields=(
    #         ('createdTime', 'created_time'),
    #     )
    # )


class CreateExperiment(graphene.Mutation):
    class Input:
        title = graphene.String(required=True)

    experiment = graphene.Field(ExperimentType)

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        experiment = ExperimentModel.objects.create(
            title=kwargs.get('title'),
            created_by=user)
        acl = ObjectACL.objects.create(
            content_object=experiment,
            pluginId="django_user",
            entityId=user.id,
            isOwner=True,
            canRead=True,
            canWrite=True,
            canDelete=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED)
        return CreateExperiment(experiment=experiment)


class UpdateExperiment(graphene.Mutation):
    class Input:
        id = graphene.Int(required=True)
        title = graphene.String(required=True)

    experiment = graphene.Field(ExperimentType)

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        experiment = ExperimentModel.objects.get(pk=kwargs.get('id'))
        if experiment.created_by != user:
            return None
        experiment.title = kwargs.get('title')
        experiment.save()
        return UpdateExperiment(experiment=experiment)
