import os
import sys

os.environ['PYTHON_EGG_CACHE'] = '~/.python-eggs'
sys.path.append('/Users/steve/Documents/myTARDIS') 
sys.path.append('/System/Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages')
sys.path.append('/System/Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages/django')

os.environ['DJANGO_SETTINGS_MODULE'] = 'tardis.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
