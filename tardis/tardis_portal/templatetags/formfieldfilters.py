'''
This module holds filters that can be used in postprocessing a form field.

@author: Gerson Galang
'''

from django import template

from lxml.html.clean import Cleaner  # pylint: disable=E0611

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


@register.filter
def sanitize_html(html, bad_tags=['body']):
    """Removes identified malicious HTML content from the given string."""
    if html is None or html == '':
        return html
    cleaner = Cleaner(style=False, page_structure=True, remove_tags=bad_tags,
                      safe_attrs_only=False)
    return cleaner.clean_html(html)
