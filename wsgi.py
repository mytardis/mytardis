
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'tardis.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
# for in-web page debugging. Highly insecure, only use temporarily
from django.conf import settings
if settings.DEBUG:
    from django.views import debug
    try:
        from django_extensions.management.technical_response import \
            null_technical_500_response
    except ImportError:
        def null_technical_500_response(request, exc_type, exc_value, tb):
            raise exc_type, exc_value, tb
    debug.technical_500_response = null_technical_500_response
    try:
        from werkzeug.debug import DebuggedApplication
        application = DebuggedApplication(application, evalex=True)
    except ImportError:
        print "Werkzeug is not installed"
