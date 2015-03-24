from django.conf import settings
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template import Context
from django.contrib.auth.models import AnonymousUser


def error_handler(request, **kwargs):
    request.user = AnonymousUser()
    context = Context({'STATIC_URL': settings.STATIC_URL,
                       'server_error': True})
    return HttpResponseServerError(
        render(request, '500.html', context))
