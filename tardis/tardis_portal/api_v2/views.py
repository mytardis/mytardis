from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from ..models.facility import Facility, facilities_managed_by
from ..models.storage import StorageBox, StorageBoxOption, StorageBoxAttribute
from ..models.instrument import Instrument
from ..models.experiment import Experiment
from ..models.dataset import Dataset
from ..models.datafile import DataFile, DataFileObject
from .permissions import (IsFacilityManager, IsFacilityManagerOf,
                          IsFacilityManagerOrReadOnly)
from .serializers import (UserSerializer, GroupSerializer,
                          FacilitySerializer, InstrumentSerializer,
                          ExperimentSerializer, DatasetSerializer,
                          DataFileSerializer, DataFileObjectSerializer,
                          StorageBoxSerializer,
                          StorageBoxOptionSerializer,
                          StorageBoxAttributeSerializer)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or listed.
    """
    queryset = User.objects.order_by('id')
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser | IsFacilityManager,)
    http_method_names = ['get', 'options', 'head']

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

    def get_queryset(self):
        if self.request.user.is_superuser:
            queryset = DataFile.objects.order_by('id')
        queryset = DataFile.objects.filter(
            dataset__experiments__in=Experiment.safe.all(
                self.request.user)
            ).order_by('id')
        directory = self.request.query_params.get('directory', None)
        if directory is not None:
            queryset = queryset.filter(directory=directory)
        filename = self.request.query_params.get('filename', None)
        if filename is not None:
            queryset = queryset.filter(filename=filename)
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
