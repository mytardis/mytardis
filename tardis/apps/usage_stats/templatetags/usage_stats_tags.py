import math

from django import template

register = template.Library()


def _get_display_unit(bytes: int) -> dict:
    """
    Given a number representing bytes, returns the unit and exponent when the
    number is scaled to one of KB, MB, GB, etc.

    e.g.
        1000    -> { 'unit': 'KB', 'exp': 3 }
        10000   -> { 'unit': 'KB', 'exp': 3 }
        5000000 -> { 'unit': 'MB', 'exp': 6 }
    """
    bytes = int(bytes)
    units = ['KB', 'MB', 'GB', 'TB', 'PB']

    actual_exp = math.floor(math.log10(bytes))
    display_unit = units[0]

    for idx, unit in enumerate(units):
        if ((idx + 1) * 3 > actual_exp) and idx != 0:
            break

        display_unit = {
            'unit': unit,
            'exp': (idx + 1) * 3,
        }

    return display_unit


def prettify_bytes(bytes):
    """
    Given a number representing bytes, returns an appropriately scaled number.
    To be used in conjuction with prettify_byte_units

    e.g.
        1000        -> 1 (KB)
        10000       -> 10 (KB)
        100000      -> 100 (KB)
        1000000     -> 1 (MB)
        10000000    -> 10 (MB)
    """
    if bytes is None or bytes == 0:
        return 0

    display_unit = _get_display_unit(bytes)

    return bytes / (10 ** display_unit['exp'])


def prettify_byte_units(bytes):
    """
    Given a number representing bytes, returns the unit of the appropriately
    scaled number. To be used in conjuction with prettify_bytes

    e.g.
        1000        -> KB
        10000       -> KB
        100000      -> KB
        1000000     -> MB
        10000000    -> MB
    """
    if bytes is None or bytes == 0:
        return ''

    display_unit = _get_display_unit(bytes)

    return display_unit['unit']


register.filter('prettify_bytes', prettify_bytes)
register.filter('prettify_byte_units', prettify_byte_units)
