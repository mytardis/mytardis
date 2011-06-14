'''
This module holds filters that can be used in postprocessing a form field.

@author: Gerson Galang
'''

from django import template


register = template.Library()


@register.filter
def size(value, actualSize):
    """Add the size attribute to the text field."""

    value.field.widget.attrs['size'] = actualSize
    return value


@register.filter
def parametername_form(value):
    "Removes all values of arg from the given string"
    return value.replace('/', '_s47_')
