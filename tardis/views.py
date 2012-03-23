from django.conf import settings
from django.shortcuts import render_to_response
from django.template import Context

def error_handler(request, **kwargs):
    context = Context({'STATIC_URL': settings.STATIC_URL,
                       'server_error': True })
    return render_to_response('500.html', context);
