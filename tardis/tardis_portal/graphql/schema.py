import graphene
from graphene_django.filter import DjangoFilterConnectionField

import graphql_jwt

from django.contrib.auth.models import Group as GroupModel

from ..models.facility import Facility as FacilityModel
from ..models.instrument import Instrument as InstrumentModel
from ..models.experiment import Experiment as ExperimentModel
from ..models.dataset import Dataset as DatasetModel

from .user import UserType, UserSignIn, ApiSignIn
from .group import GroupType
from .facility import FacilityType
from .instrument import InstrumentType
from .experiment import ExperimentType, ExperimentTypeFilter
from .dataset import DatasetType


class Query(graphene.ObjectType):

    user = graphene.Field(UserType)
    def resolve_user(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None

    groups = DjangoFilterConnectionField(GroupType)
    def resolve_groups(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated and user.is_superuser:
            return GroupModel.objects.all()
        return GroupModel.objects.none()

    facilities = DjangoFilterConnectionField(FacilityType)
    def resolve_facilities(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated and user.is_superuser:
            return FacilityModel.objects.all()
        return FacilityModel.objects.filter(manager_group__user=user)

    instruments = DjangoFilterConnectionField(InstrumentType)
    def resolve_instruments(self, info, **kwargs):
        user = info.context.user
        facilities = FacilityModel.objects.filter(manager_group__user=user)
        return InstrumentModel.objects.filter(facility__in=facilities)

    experiments = DjangoFilterConnectionField(ExperimentType, filterset_class=ExperimentTypeFilter)
    def resolve_experiments(self, info, **kwargs):
        user = info.context.user
        return ExperimentModel.safe.all(user)

    datasets = DjangoFilterConnectionField(DatasetType)
    def resolve_datasets(self, info, **kwargs):
        user = info.context.user
        experiments = ExperimentModel.safe.all(user)
        return DatasetModel.objects.filter(experiments__in=experiments)


class Mutation(graphene.ObjectType):
    verify_token = graphql_jwt.relay.Verify.Field()
    refresh_token = graphql_jwt.relay.Refresh.Field()
    revoke_token = graphql_jwt.relay.Revoke.Field()

    user_sign_in = UserSignIn.Field()
    api_key_sign_in = ApiSignIn.Field()

    # create_experiment = CreateExperiment.Field()
    # update_experiment = UpdateExperiment.Field()
