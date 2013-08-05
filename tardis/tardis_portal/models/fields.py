'''
custom model fields
'''

from django.db import models
from django import forms

from south.modelsinspector import add_introspection_rules
add_introspection_rules(
    [], ["^tardis\.tardis_portal\.models\.fields\.DirectoryField"])


class DirectoryField(models.TextField):
    '''
    Directories should never be presented in a text area
    This class also allows for future customisations
    In case you wonder why there is no character limit:
      - Most filesystems don't impose a limit
      - Postgres performance is not affected by the size of the field
    '''

    def formfield(self, **kwargs):
        defaults = {'widget': forms.TextInput}
        defaults.update(kwargs)
        return super(DirectoryField, self).formfield(**defaults)
