from django.conf import settings
import haystack

if 'haystack' in settings.INSTALLED_APPS:
    haystack.autodiscover()
