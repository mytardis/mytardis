from .server import get_server


def endpoint(request):
    return get_server().handleRequest(request.REQUEST)