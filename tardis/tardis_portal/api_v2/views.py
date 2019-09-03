from django.contrib.auth.models import User, Group
from rest_framework import viewsets

from ..models.facility import Facility, facilities_managed_by
from .permissions import IsSuperUser, IsFacilityManager, IsFacilityManagerOf
from .serializers import (UserSerializer, GroupSerializer,
                          FacilitySerializer)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.order_by('id')
    serializer_class = UserSerializer
    permission_classes = (IsSuperUser|IsFacilityManager,)
    http_method_names = ['get', 'options', 'head']


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.order_by('id')
    serializer_class = GroupSerializer
    permission_classes = (IsSuperUser|IsFacilityManager,)
    http_method_names = ['get', 'options', 'head']


class FacilityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows facilities to be viewed or edited.
    """
    queryset = Facility.objects.order_by('id')
    serializer_class = FacilitySerializer
    http_method_names = ['get', 'options', 'head']
    permission_classes = (IsSuperUser|(IsFacilityManager&IsFacilityManagerOf),)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Facility.objects.order_by('id')
        return facilities_managed_by(self.request.user)
