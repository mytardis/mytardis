from django.conf import settings
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template import Context


def error_handler(request, **kwargs):
    context = Context({'STATIC_URL': settings.STATIC_URL,
                       'server_error': True})
    return HttpResponseServerError(
        render(request, '500.html', context))
