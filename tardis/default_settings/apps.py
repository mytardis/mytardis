# A tuple of strings designating all applications that are enabled in
# this Django installation.
TARDIS_APP_ROOT = 'tardis.apps'
INSTALLED_APPS = (
    'django_extensions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',
    'registration',
    'jstemplate',
    'graphene_django',
    'django_filters',
    'crispy_forms', # required for django_filters
    'corsheaders',
    'tastypie',
    'tastypie_swagger',
    'webpack_loader',
    'widget_tweaks',
    'tardis.tardis_portal',
    'tardis.tardis_portal.templatetags',
    'tardis.analytics',
    # these optional apps, may require extra settings
    'tardis.apps.publication_workflow',
    'tardis.apps.oaipmh',
    'tardis.apps.sftp',
    # 'tardis.apps.push_to',
    # 'tardis.apps.social_auth',
)

USER_MENU_MODIFIERS = []
'''
A list of methods which can modify the user menu defined in
tardis.tardis_portal.context_processors.user_menu_processor
The modifications will be applied in order, so it is possible for one
app to overwrite changes made by another app whose modifier method is
earlier in the list.

Each modifier method should take a django.http.HttpRequest object and a
list of user menu items, and return a modified list of user menu items.

An example from the SFTP app is below::

  USER_MENU_MODIFIERS.extend([
      'tardis.apps.sftp.user_menu_modifiers.add_ssh_keys_menu_item'
  ])
'''
