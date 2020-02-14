import graphene
from graphene_django.filter import DjangoFilterConnectionField

import graphql_jwt

from django.contrib.auth.models import Group as GroupModel

from ..models.facility import Facility as FacilityModel
from ..models.instrument import Instrument as InstrumentModel
from ..models.dataset import Dataset as DatasetModel
from ..models.datafile import (
    DataFileObject as DataFileObjectModel
)
from ..models.storage import (
    StorageBox as StorageBoxModel,
    StorageBoxOption as StorageBoxOptionModel,
    StorageBoxAttribute as StorageBoxAttributeModel
)

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
from .datafile import (
    DataFileType, DataFileTypeFilter,
    CreateDataFile, UpdateDataFile
)
from .datafileobject import (
    DataFileObjectType, DataFileObjectTypeFilter,
    CreateDataFileObject, UpdateDataFileObject
)
from .storagebox import (
    StorageBoxType, StorageBoxTypeFilter,
    CreateStorageBox, UpdateStorageBox
)
from .storageboxoption import (
    StorageBoxOptionType, StorageBoxOptionTypeFilter,
    CreateStorageBoxOption, UpdateStorageBoxOption
)
from .storageboxattribute import (
    StorageBoxAttributeType, StorageBoxAttributeTypeFilter,
    CreateStorageBoxAttribute, UpdateStorageBoxAttribute
)
from .utils import (
    get_accessible_experiments,
    get_accessible_datafiles
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
            return get_accessible_experiments(user)
        return None

    datasets = DjangoFilterConnectionField(
        DatasetType,
        filterset_class=DatasetTypeFilter
    )
    def resolve_datasets(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            return DatasetModel.objects.filter(
                experiments__in=get_accessible_experiments(user)
            )
        return None

    datafiles = DjangoFilterConnectionField(
        DataFileType,
        filterset_class=DataFileTypeFilter
    )
    def resolve_datafiles(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            return get_accessible_datafiles(user)
        return None

    datafileobjects = DjangoFilterConnectionField(
        DataFileObjectType,
        filterset_class=DataFileObjectTypeFilter
    )
    def resolve_datafileobjects(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            return DataFileObjectModel.objects.filter(
                datafile__in=get_accessible_datafiles(user)
            )
        return None

    storageboxes = DjangoFilterConnectionField(
        StorageBoxType,
        filterset_class=StorageBoxTypeFilter
    )
    def resolve_storageboxes(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            if user.is_superuser:
                return StorageBoxModel.objects.all()
        return None

    storageboxoptions = DjangoFilterConnectionField(
        StorageBoxOptionType,
        filterset_class=StorageBoxOptionTypeFilter
    )
    def resolve_storageboxoptions(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            if user.is_superuser:
                return StorageBoxOptionModel.objects.all()
        return None

    storageboxattributes = DjangoFilterConnectionField(
        StorageBoxAttributeType,
        filterset_class=StorageBoxAttributeTypeFilter
    )
    def resolve_storageboxattributes(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            if user.is_superuser:
                return StorageBoxAttributeModel.objects.all()
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

    create_datafile = CreateDataFile.Field()
    update_datafile = UpdateDataFile.Field()

    create_datafileobject = CreateDataFileObject.Field()
    update_datafileobject = UpdateDataFileObject.Field()

    create_storagebox = CreateStorageBox.Field()
    update_storagebox = UpdateStorageBox.Field()

    create_storageboxoption = CreateStorageBoxOption.Field()
    update_storageboxoption = UpdateStorageBoxOption.Field()

    create_storageboxattribute = CreateStorageBoxAttribute.Field()
    update_storageboxattribute = UpdateStorageBoxAttribute.Field()
