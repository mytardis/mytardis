import sys
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
    :attribute priority: a priority score that is used to rank the locations
        when deciding which one to use
    :attribute is_available: if True, the location should currently be
        accessible / useable

    ... and other attributes TBD
    '''

    name = models.CharField(max_length=10, unique=True)
    url = models.CharField(max_length=400, unique=True)
    type = models.CharField(max_length=10)
    priority = models.IntegerField()
    is_available = models.BooleanField(default=True)
    trust_length = models.BooleanField(default=False)
    metadata_supported = models.BooleanField(default=False)
    auth_user = models.CharField(max_length=20, default='')
    auth_password = models.CharField(max_length=400, default='')
    auth_realm = models.CharField(max_length=20, default='')
    auth_scheme = models.CharField(max_length=10, default='digest')
    migration_provider = models.CharField(max_length=10, default='local')

    initialized = False

    class Meta:
        app_label = 'tardis_portal'

    def get_priority(self):
        '''Return the location's priority, or -1 if it is not available'''
        if self.is_available:
            return self.priority
        else:
            return -1

    @classmethod
    def get_default_location(cls):
        '''Lookup the default location'''
        return Location.get_location(settings.DEFAULT_LOCATION)

    @classmethod
    def get_location(cls, loc_name):
        '''Lookup a named location'''

        cls._check_initialized()
        try:
            return Location.objects.get(name=loc_name)
        except Location.DoesNotExist:
            return None

    @classmethod
    def get_location_for_url(cls, url):
        '''Reverse lookup a location from a url'''
        
        cls._check_initialized()
        for location in Location.objects.all():
            if url.startswith(location.url):
                return location
        return None

    @classmethod
    def _check_initialized(cls):
        if not cls.initialized:
            cls.force_initialize()
        cls.initialized = True

    @classmethod
    def force_initialize(cls):
        for desc in settings.INITIAL_LOCATIONS:
            try:
                Location.objects.get(name=desc['name'])
            except Location.DoesNotExist:
                url = desc['url']
                if not url.endswith('/'):
                    url = url + '/'
                location = Location(
                    name=desc['name'],
                    url=url,
                    type=desc['type'],
                    priority=desc['priority'],
                    migration_provider=desc.get('provider', 'local'),
                    trust_length=desc.get('trust_length', False),
                    metadata_supported=desc.get('metadata_supported', False),
                    auth_user=desc.get('user', ''),
                    auth_password=desc.get('password', ''),
                    auth_realm=desc.get('realm', ''),
                    auth_scheme=desc.get('scheme', 'digest'))
                location.save()

    def __unicode__(self):
        return self.name

