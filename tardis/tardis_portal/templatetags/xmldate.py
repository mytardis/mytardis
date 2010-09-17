from django import template
from datetime import datetime
from tardis.tardis_portal.rfc3339 import rfc3339

register = template.Library()


@register.filter
def toxmldatetime(value):
    return rfc3339(value)
