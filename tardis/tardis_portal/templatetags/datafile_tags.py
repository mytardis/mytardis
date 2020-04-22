from django import template
from ..auth import decorators as authz
register = template.Library()


@register.simple_tag
def is_datafile_downloadable(datafile_id, request):
    """
    Determines if Datafile is downloadable by User, respecting ACLs
    """
    has_download_permissions = authz.has_datafile_download_access(request,datafile_id)

    return has_download_permissions


@register.simple_tag
def is_datafile_writable(datafile_id, request):
    """
    Determines if Datafile is writable by User, respecting ACLs
    """
    has_write_permissions = authz.has_datafile_write(request,datafile_id)

    return has_write_permissions
