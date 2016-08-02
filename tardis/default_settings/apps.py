# A tuple of strings designating all applications that are enabled in
# this Django installation.
TARDIS_APP_ROOT = 'tardis.apps'
INSTALLED_APPS = (
    'django_extensions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',
    'registration',
    'django_jasmine',
    'djcelery',
    'kombu.transport.django',
    'bootstrapform',
    'mustachejs',
    'tastypie',
    'tastypie_swagger',
    'tardis.tardis_portal',
    'tardis.tardis_portal.templatetags',
    'tardis.search',
    'tardis.analytics',
    # these optional apps, may require extra settings
    'tardis.apps.publication_forms',
    'tardis.apps.oaipmh',
    # 'tardis.apps.push_to',
)
