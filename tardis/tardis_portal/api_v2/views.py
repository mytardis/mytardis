import django_filters
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from ..models.facility import Facility, facilities_managed_by
from ..models.storage import StorageBox, StorageBoxOption, StorageBoxAttribute
from ..models.instrument import Instrument
from ..models.experiment import Experiment
from ..models.dataset import Dataset
from ..models.datafile import DataFile, DataFileObject
from ..models.parameters import (Schema, ParameterName,
                                 ExperimentParameterSet, ExperimentParameter)

from .permissions import (IsFacilityManager, IsFacilityManagerOf,
                          IsFacilityManagerOrReadOnly)

from .serializers import (UserSerializer, GroupSerializer,
                          FacilitySerializer, InstrumentSerializer,
                          ExperimentSerializer, DatasetSerializer,
                          DataFileSerializer, DataFileObjectSerializer,
                          StorageBoxSerializer,
                          StorageBoxOptionSerializer,
                          StorageBoxAttributeSerializer,
                          SchemaSerializer, ParameterNameSerializer,
                          ExperimentParameterSetSerializer,
                          ExperimentParameterSerializer)


class UserFilter(django_filters.FilterSet):
    email__iexact = django_filters.CharFilter(field_name='email', lookup_expr='iexact')
    class Meta:
        model = User
        fields = ('username', 'email')

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or listed.
    """
    queryset = User.objects.order_by('id')
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser | IsFacilityManager,)
    http_method_names = ['get', 'options', 'head']
    filterset_class = UserFilter
    filter_fields = ('username', 'email',)

    def get_queryset(self):
        if facilities_managed_by(self.request.user).count():
            return User.objects.order_by('id')
        return User.objects.filter(id=self.request.user.id).order_by('id')


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or listed.
    """
    queryset = Group.objects.order_by('id')
    serializer_class = GroupSerializer
    permission_classes = (IsAdminUser | IsFacilityManager,)
    http_method_names = ['get', 'options', 'head']


class StorageBoxViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows storage boxes to be viewed or listed.
    """
    queryset = StorageBox.objects.order_by('id')
    serializer_class = StorageBoxSerializer
    permission_classes = (IsAdminUser | IsFacilityManager,)
    http_method_names = ['get', 'options', 'head']


class StorageBoxOptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows storage box options to be viewed or listed.
    """
    queryset = StorageBoxOption.objects.order_by('id')
    serializer_class = StorageBoxOptionSerializer
    permission_classes = (IsAdminUser | IsFacilityManager,)
    http_method_names = ['get', 'options', 'head']

    def get_queryset(self):
        if self.request.user.is_superuser:
            return StorageBoxOption.objects.order_by('id')
        # StorageBoxOptions are the keyword parameters passed to Django
        # storage classes (e.g. access_key, secret_key) to instantiate
        # storage instances. To make a StorageBoxOption available to
        # non-admin users via the API, it needs to be whitelisted here:
        allowed_keys = ['location']
        return StorageBoxOption.objects.filter(
            key__in=allowed_keys).order_by('id')


class StorageBoxAttributeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows storage box attributes to be viewed or listed.
    """
    queryset = StorageBoxAttribute.objects.order_by('id')
    serializer_class = StorageBoxAttributeSerializer
    permission_classes = (IsAdminUser | IsFacilityManager,)
    http_method_names = ['get', 'options', 'head']


class FacilityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows facilities to be viewed or listed.
    """
    queryset = Facility.objects.order_by('id')
    serializer_class = FacilitySerializer
    http_method_names = ['get', 'options', 'head']
    permission_classes = (IsAdminUser | (IsFacilityManager & IsFacilityManagerOf),)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Facility.objects.order_by('id')
        return facilities_managed_by(self.request.user)


class InstrumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows instruments to be viewed, created or edited.
    """
    queryset = Instrument.objects.order_by('id')
    serializer_class = InstrumentSerializer
    http_method_names = ['get', 'options', 'head', 'post', 'patch', 'put']
    permission_classes = (IsAuthenticated & IsFacilityManagerOrReadOnly,)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Instrument.objects.order_by('id')
        return Instrument.objects.filter(
            facility__in=facilities_managed_by(self.request.user)).order_by('id')


class ExperimentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows experiments to be viewed, created or edited.
    """
    queryset = Experiment.objects.order_by('id')
    serializer_class = ExperimentSerializer
    http_method_names = ['get', 'options', 'head', 'post', 'patch', 'put']
    permission_classes = (AllowAny,)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Experiment.objects.order_by('id')
        return Experiment.safe.all(self.request.user).order_by('id')


class DatasetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows datasets to be viewed, created or edited.
    """
    queryset = Dataset.objects.order_by('id')
    serializer_class = DatasetSerializer
    http_method_names = ['get', 'options', 'head', 'post', 'patch', 'put']
    permission_classes = (AllowAny,)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Dataset.objects.order_by('id')
        return Dataset.objects.filter(
            experiments__in=Experiment.safe.all(
                self.request.user)
            ).order_by('id')


class DataFileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows datafiles to be viewed, created or edited.
    """
    queryset = DataFile.objects.order_by('id')
    serializer_class = DataFileSerializer
    http_method_names = ['get', 'options', 'head', 'post', 'patch', 'put']
    permission_classes = (AllowAny,)
    filter_fields = ('dataset__id', 'directory', 'filename',)

    def get_queryset(self):
        if self.request.user.is_superuser:
            queryset = DataFile.objects.order_by('id')
        queryset = DataFile.objects.filter(
            dataset__experiments__in=Experiment.safe.all(
                self.request.user)
            ).order_by('id')
        return queryset


class DataFileObjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows datafile objects to be viewed, created or edited.
    """
    queryset = DataFileObject.objects.order_by('id')
    serializer_class = DataFileObjectSerializer
    http_method_names = ['get', 'options', 'head', 'post', 'patch', 'put']
    permission_classes = (AllowAny,)

    def get_queryset(self):
        if self.request.user.is_superuser:
            queryset = DataFileObject.objects.order_by('id')
        queryset = DataFileObject.objects.filter(
            datafile__dataset__experiments__in=Experiment.safe.all(
                self.request.user)
            ).order_by('id')
        return queryset


class SchemaViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows metadata schemas to be viewed or listed.
    """
    queryset = Schema.objects.order_by('id')
    serializer_class = SchemaSerializer
    permission_classes = (AllowAny,)
    http_method_names = ['get', 'options', 'head']

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Schema.objects.order_by('id')
        return Schema.objects.filter(hidden=False).order_by('id')


class ParameterNameViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows metadata parameter names to be viewed or listed.
    """
    queryset = ParameterName.objects.order_by('id')
    serializer_class = ParameterNameSerializer
    permission_classes = (AllowAny,)
    http_method_names = ['get', 'options', 'head']
    filter_fields = ('name', 'schema__id',)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return ParameterName.objects.order_by('id')
        return ParameterName.objects.filter(schema__hidden=False).order_by('id')


class ExperimentParameterSetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows experiment metadata parameter sets to be viewed or
    listed.
    """
    queryset = ExperimentParameterSet.objects.order_by('id')
    serializer_class = ExperimentParameterSetSerializer
    permission_classes = (AllowAny,)
    http_method_names = ['get', 'options', 'head']
    filter_fields = ('experiment__id', 'schema__id',)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return ExperimentParameterSet.objects.order_by('id')
        return ExperimentParameterSet.objects.filter(
            schema__hidden=False,
            experiment__in=Experiment.safe.all(self.request.user)
        ).order_by('id')


class ExperimentParameterViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows experiment metadata parameters to be viewed or
    listed.
    """
    queryset = ExperimentParameter.objects.order_by('id')
    serializer_class = ExperimentParameterSerializer
    permission_classes = (AllowAny,)
    http_method_names = ['get', 'options', 'head']

    def get_queryset(self):
        if self.request.user.is_superuser:
            return ExperimentParameter.objects.order_by('id')
        return ExperimentParameter.objects.filter(
            parameterset__schema__hidden=False,
            parameterset__experiment__in=Experiment.safe.all(self.request.user)
        ).order_by('id')
