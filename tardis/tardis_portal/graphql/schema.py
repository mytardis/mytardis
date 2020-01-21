import graphene
from graphene import Node
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.debug import DjangoDebug
from graphql import GraphQLError

import graphql_jwt

from ..models.facility import Facility as FacilityModel, facilities_managed_by
from ..models.instrument import Instrument as InstrumentModel
from ..models.experiment import Experiment as ExperimentModel
from ..models.dataset import Dataset as DatasetModel

from .user import UserType, UserSignIn
from .facility import FacilityType
from .instrument import InstrumentType
from .experiment import ExperimentType, CreateExperiment, UpdateExperiment
from .dataset import DatasetType


class Query(graphene.ObjectType):

    user = graphene.Field(UserType)
    def resolve_user(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None

    facilities = DjangoFilterConnectionField(FacilityType)
    def resolve_facilities(self, info, **kwargs):
        user = info.context.user
        return facilities_managed_by(user)

    instruments = DjangoFilterConnectionField(InstrumentType)
    def resolve_instruments(self, info, **kwargs):
        user = info.context.user
        facilities = facilities_managed_by(user)
        return InstrumentModel.objects.filter(facility__in=facilities)

    experiments = DjangoFilterConnectionField(ExperimentType)
    def resolve_experiments(self, info, **kwargs):
        user = info.context.user
        return ExperimentModel.safe.all(user)

    datasets = DjangoFilterConnectionField(DatasetType)
    def resolve_datasets(self, info, **kwargs):
        user = info.context.user
        experiments = ExperimentModel.safe.all(user)
        return DatasetModel.objects.filter(experiments__in=experiments)


class Mutation(graphene.ObjectType):
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

    user_sign_in = UserSignIn.Field()

    # create_experiment = CreateExperiment.Field()
    # update_experiment = UpdateExperiment.Field()
