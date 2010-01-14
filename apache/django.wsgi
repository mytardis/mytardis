import os
import sys

sys.path.append('/Users/steve/django-jython-svn/myTARDIS_checkout')
os.environ['DJANGO_SETTINGS_MODULE'] = 'tardis.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()