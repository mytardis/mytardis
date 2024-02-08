from django import template


def get_item(dictionary, key):
    """Returns a value from a dictionary."""
    return dictionary.get(key)


register = template.Library()
register.filter("get_item", get_item)
