from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseServerError
from django.shortcuts import render


def error_handler(request, **kwargs):
    request.user = AnonymousUser()
    context = {"STATIC_URL": settings.STATIC_URL, "server_error": True}
    return HttpResponseServerError(render(request, "500.html", context))
