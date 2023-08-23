from django import template

register = template.Library()


def floatdivideby(value, arg):
    """Divides by arg"""
    return float(float(value) / arg)


register.filter('floatdivideby', floatdivideby)
