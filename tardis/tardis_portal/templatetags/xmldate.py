from django import template

from ..rfc3339 import rfc3339

register = template.Library()


@register.filter
def toxmldatetime(value):
    return rfc3339(value)
