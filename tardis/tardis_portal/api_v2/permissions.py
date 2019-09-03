from rest_framework import permissions

from ..models.facility import facilities_managed_by


class IsSuperUser(permissions.BasePermission):
    """
    Permission representing Django superusers
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


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
