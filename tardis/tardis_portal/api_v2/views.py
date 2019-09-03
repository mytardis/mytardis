from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from ..models.facility import Facility, facilities_managed_by
from ..models.instrument import Instrument
from ..models.experiment import Experiment
from .permissions import (IsFacilityManager, IsFacilityManagerOf,
                          IsFacilityManagerOrReadOnly)
from .serializers import (UserSerializer, GroupSerializer,
                          FacilitySerializer, InstrumentSerializer,
                          ExperimentSerializer)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or listed.
    """
    queryset = User.objects.order_by('id')
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser|IsFacilityManager,)
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
    permission_classes = (IsAdminUser|IsFacilityManager,)
    http_method_names = ['get', 'options', 'head']


class FacilityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows facilities to be viewed or listed.
    """
    queryset = Facility.objects.order_by('id')
    serializer_class = FacilitySerializer
    http_method_names = ['get', 'options', 'head']
    permission_classes = (IsAdminUser|(IsFacilityManager&IsFacilityManagerOf),)

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
    permission_classes = (IsAuthenticated&IsFacilityManagerOrReadOnly,)

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
