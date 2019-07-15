from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from .permissions import IsSuperUser, IsFacilityManager
from .serializers import UserSerializer, GroupSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.order_by('id')
    serializer_class = UserSerializer
    permission_classes = (IsSuperUser|IsFacilityManager,)


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.order_by('id')
    serializer_class = GroupSerializer
    permission_classes = (IsSuperUser|IsFacilityManager,)
