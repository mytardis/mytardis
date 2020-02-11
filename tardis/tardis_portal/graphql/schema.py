import graphene
from graphene_django.filter import DjangoFilterConnectionField

import graphql_jwt

from django.contrib.auth.models import Group as GroupModel

from ..models.facility import Facility as FacilityModel
from ..models.instrument import Instrument as InstrumentModel
from ..models.experiment import Experiment as ExperimentModel
from ..models.dataset import Dataset as DatasetModel

from .user import UserType, UserSignIn, ApiSignIn
from .group import (
    GroupType, GroupTypeFilter,
    CreateGroup, UpdateGroup
)
from .facility import (
    FacilityType, FacilityTypeFilter,
    CreateFacility, UpdateFacility
)
from .instrument import (
    InstrumentType, InstrumentTypeFilter,
    CreateInstrument, UpdateInstrument
)
from .experiment import (
    ExperimentType, ExperimentTypeFilter,
    CreateExperiment, UpdateExperiment
)
from .dataset import (
    DatasetType, DatasetTypeFilter,
    CreateDataset, UpdateDataset
)


class Query(graphene.ObjectType):

    user = graphene.Field(UserType)
    def resolve_user(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None

    groups = DjangoFilterConnectionField(
        GroupType,
        filterset_class=GroupTypeFilter
    )
    def resolve_groups(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            if user.is_superuser:
                return GroupModel.objects.all()
            return GroupModel.objects.filter(user=user)
        return None

    facilities = DjangoFilterConnectionField(
        FacilityType,
        filterset_class=FacilityTypeFilter
    )
    def resolve_facilities(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            if user.is_superuser:
                return FacilityModel.objects.all()
            return FacilityModel.objects.filter(manager_group__user=user)
        return None

    instruments = DjangoFilterConnectionField(
        InstrumentType,
        filterset_class=InstrumentTypeFilter
    )
    def resolve_instruments(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            if user.is_superuser:
                return InstrumentModel.objects.all()
            facilities = FacilityModel.objects.filter(manager_group__user=user)
            return InstrumentModel.objects.filter(facility__in=facilities)
        return None

    experiments = DjangoFilterConnectionField(
        ExperimentType,
        filterset_class=ExperimentTypeFilter
    )
    def resolve_experiments(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            return ExperimentModel.safe.all(user)
        return None

    datasets = DjangoFilterConnectionField(
        DatasetType,
        filterset_class=DatasetTypeFilter
    )
    def resolve_datasets(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            experiments = ExperimentModel.safe.all(user)
            return DatasetModel.objects.filter(experiments__in=experiments)
        return None


class Mutation(graphene.ObjectType):
    verify_token = graphql_jwt.relay.Verify.Field()
    refresh_token = graphql_jwt.relay.Refresh.Field()
    revoke_token = graphql_jwt.relay.Revoke.Field()

    user_sign_in = UserSignIn.Field()
    api_key_sign_in = ApiSignIn.Field()

    create_group = CreateGroup.Field()
    update_group = UpdateGroup.Field()

    create_facility = CreateFacility.Field()
    update_facility = UpdateFacility.Field()

    create_instrument = CreateInstrument.Field()
    update_instrument = UpdateInstrument.Field()

    create_experiment = CreateExperiment.Field()
    update_experiment = UpdateExperiment.Field()

    create_dataset = CreateDataset.Field()
    update_dataset = UpdateDataset.Field()
