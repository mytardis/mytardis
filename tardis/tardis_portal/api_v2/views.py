from django.contrib.auth.models import User, Group
from rest_framework import viewsets

from ..models.facility import Facility, facilities_managed_by
from ..models.instrument import Instrument
from .permissions import (IsSuperUser, IsFacilityManager, IsFacilityManagerOf,
                          IsAuthenticated, IsFacilityManagerOrReadOnly)
from .serializers import (UserSerializer, GroupSerializer,
                          FacilitySerializer, InstrumentSerializer)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or listed.
    """
    queryset = User.objects.order_by('id')
    serializer_class = UserSerializer
    permission_classes = (IsSuperUser|IsFacilityManager,)
    http_method_names = ['get', 'options', 'head']


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or listed.
    """
    queryset = Group.objects.order_by('id')
    serializer_class = GroupSerializer
    permission_classes = (IsSuperUser|IsFacilityManager,)
    http_method_names = ['get', 'options', 'head']


class FacilityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows facilities to be viewed or listed.
    """
    queryset = Facility.objects.order_by('id')
    serializer_class = FacilitySerializer
    http_method_names = ['get', 'options', 'head']
    permission_classes = (IsSuperUser|(IsFacilityManager&IsFacilityManagerOf),)

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
            facility__in=facilities_managed_by(self.request.user))
