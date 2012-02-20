from .server import get_server
from django.http import HttpResponse


def endpoint(request):
    return HttpResponse(get_server().handleRequest(request.REQUEST), 200)