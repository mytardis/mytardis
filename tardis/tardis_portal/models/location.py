from django.conf import settings
from django.db import models
from django.core.files.storage import default_storage



import logging
logger = logging.getLogger(__name__)

class Location(models.Model):
    '''Class to store metadata about a storage location

    :attribute name: the name for the location
    :attribute url: the url for the location
    :attribute type: one of 'online', 'offline' and 'external'

    ... and other attributes TBD
    '''

    def get_priority(self):
        # Temporary hack ...
        return 1

    name = models.CharField(max_length=10)
    url = models.CharField(max_length=400)
    type = models.CharField(max_length=10)
    priority = property(get_priority)

    class Meta:
        app_label = 'tardis_portal'

    @classmethod
    def get_default_location(cls):
        return Location.get_location(settings.DEFAULT_LOCATION)

    @classmethod
    def get_location(cls, loc_name, retrying=False):
        try:
            return Location.objects.get(name=loc_name)
        except Location.DoesNotExist:
            # Lazy initialization.  We could use a 'fixture' but then
            # it would be difficult to integrate with other stuff in the 
            # settings file; e.g. the store and staging directory pathnames.
            if not retrying and \
                    (loc_name == settings.DEFAULT_LOCATION or \
                     not Location.get_location(settings.DEFAULT_LOCATION, \
                                                   retrying=True)):
                for desc in settings.INITIAL_LOCATIONS:
                    Location.objects.get_or_create(name=desc['name'],
                                                   url=desc['url'],
                                                   type=desc['type'])
                return Location.get_location(loc_name, retrying=True)
