from django.template import Context
from django.http import HttpResponse

from tardis.tardis_portal.shortcuts import render_response_index
from tardis.tardis_portal.views import *

def index_mt(request):
    status = ''

    c = Context({'status': status})
    return HttpResponse(render_response_index(request,
                        'index_mt.html', c))

def about_mt(request):
    c = Context({'subtitle': 'About',
                 'about_pressed': True,
                 'nav': [{'name': 'About', 'link': '/about/'}]})
    
    return HttpResponse(render_response_index(request,
                        'about_mt.html', c))
    
def partners_mt(request):
    c = Context({})
    
    return HttpResponse(render_response_index(request,
                        'partners_mt.html', c))