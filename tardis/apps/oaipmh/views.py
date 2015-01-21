from .server import get_server
from django.contrib.sites.models import get_current_site
from django.http import HttpResponse


def endpoint(request):
    return HttpResponse(get_server(get_current_site(request))
                        .handleRequest(request.REQUEST),
                        content_type='application/xml', status=200)
