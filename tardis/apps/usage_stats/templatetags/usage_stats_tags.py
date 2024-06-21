from django import template

register = template.Library()


def intdivideby(value, arg):
    """Divides by arg"""
    return int(int(value) / arg)


register.filter('intdivideby', intdivideby)
