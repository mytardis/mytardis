from django import template

from ..auth import decorators as authz

register = template.Library()

@register.simple_tag
def is_datafile_downloadable(datafile_id, request):
    """
    Determines if Datafile is downloadable by User, respecting ACLs
    """
    has_download_permissions = authz.has_download_access(request, datafile_id,
                                                         "datafile")
    return has_download_permissions


@register.simple_tag
def is_datafile_writable(datafile_id, request):
    """
    Determines if Datafile is writable by User, respecting ACLs
    """
    has_write_permissions = authz.has_write(request, datafile_id, "datafile")
    return has_write_permissions


@register.simple_tag
def view_sensitive_datafile(datafile_id, request):
    """
    Determines if sensitive Datafile metadata visible by User, respecting ACLs
    """
    has_sensitive_permissions = authz.has_sensitive_access(request, datafile_id, "datafile")

    return has_sensitive_permissions
