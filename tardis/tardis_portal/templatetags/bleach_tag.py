import bleach

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

tags = getattr(settings, 'BLEACH_ALLOWED_TAGS', bleach.ALLOWED_TAGS)
attributes = getattr(settings, 'BLEACH_ALLOWED_ATTRIBUTES', bleach.ALLOWED_ATTRIBUTES)


def bleach_value(value):
    bleached_value = bleach.clean(value, tags=tags)
    return mark_safe(bleached_value)

register.filter('bleach', bleach_value)
