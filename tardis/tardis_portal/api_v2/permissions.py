from rest_framework import permissions

from ..models.facility import facilities_managed_by


class IsFacilityManager(permissions.BasePermission):
    """
    Custom permission only allow facility managers
    """

    def has_permission(self, request, view):
        return request.user and facilities_managed_by(request.user).count()


class IsFacilityManagerOf(permissions.BasePermission):
    """
    Custom permission only allow facility managers
    """

    def has_object_permission(self, request, view, obj):
        return (request.user and
                facilities_managed_by(request.user).filter(pk=obj.id).exists())


class IsFacilityManagerOrReadOnly(permissions.BasePermission):
    """
    Non-facility managers can only perform read-only instrument queries
    """

    def has_permission(self, request, view):
        if (request.method in permissions.SAFE_METHODS or
            (request.user and
             facilities_managed_by(request.user))):
            return True
        return False
