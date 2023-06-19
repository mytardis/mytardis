from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse

from .server import get_server


def endpoint(request):
    return HttpResponse(get_server(get_current_site(request))
                        .handleRequest(request.GET),
                        content_type='application/xml', status=200)
