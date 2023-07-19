from django import template

from ..models.facility import is_facility_manager

register = template.Library()


@register.filter
def check_if_facility_manager(request):
    """
    Custom template filter to identify whether a user is a
    facility manager.
    """
    if (request.user.is_authenticated):
        return is_facility_manager(request.user)
    return False
