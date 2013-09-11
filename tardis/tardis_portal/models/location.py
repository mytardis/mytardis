import sys, urllib2
from django.conf import settings
from django.db import models
from django.core.files.storage import default_storage

import logging
logger = logging.getLogger(__name__)

class LocationManager():
    """
    Added by Sindhu Emilda for natural key implementation.
    The manager for the tardis_portal's Location model.
    """
    def get_by_natural_key(self, name, url):
        return self.get(name=name, url=url)

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
    transfer_provider = models.CharField(max_length=10, default='local')

    ''' Added by Sindhu Emilda for natural key implementation '''
    objects = LocationManager()
    
    def natural_key(self):
        return (self.nase,) + (self.url,)

    initialized = False

    class Meta:
        app_label = 'tardis_portal'

    def __init__(self, *args, **kwargs):
        super(Location, self).__init__(*args, **kwargs)
        self._provider = None

    def _get_provider(self):
        if not self._provider:
            self._provider = Location.build_provider(self)
        return self._provider

    provider = property(_get_provider)

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

        try:
            return Location.objects.get(name=loc_name)
        except Location.DoesNotExist:
            if not cls._check_initialized():
                return cls.get_location(loc_name)
            else:
                return None

    @classmethod
    def get_location_for_url(cls, url):
        '''Reverse lookup a location from a url'''

        for location in Location.objects.all():
            if url.startswith(location.url):
                return location
        if not cls._check_initialized():
            return cls.get_location_for_url(url)
        else:
            return None

    @classmethod
    def _check_initialized(cls):
        '''Attempt to initialize if we need to'''
        if cls.initialized:
            return True
        res = cls.force_initialize()
        cls.initialized = True
        return res

    @classmethod
    def force_initialize(cls):
        done_init = False
        for desc in settings.INITIAL_LOCATIONS:
            try:
                logger.debug('Checking location %s' % desc['name'])
                Location.objects.get(name=desc['name'])
                logger.debug('Location %s already exists' % desc['name'])
            except Location.DoesNotExist:
                Location.load_location(desc, check=False)
                logger.info('Location %s loaded' % desc['name'])
                done_init = True
        return done_init

    @classmethod
    def load_location(cls, desc, noslash=False, check=True):
        if check:
            try:
                return Location.objects.get(name=desc['name'])
            except Location.DoesNotExist:
                pass
        url = desc['url']
        if not noslash and not url.endswith('/'):
            url = url + '/'
        location = Location(name=desc['name'], url=url, type=desc['type'],
                            priority=desc['priority'],
                            transfer_provider=desc.get('provider', 'local'))
        location.save()
        for (name, value) in desc.get('params', {}).items():
            param = ProviderParameter(location=location,
                                      name=name, value=value)
            param.save()
        return location


    @classmethod
    def build_provider(cls, loc):
        params = {}
        for p in ProviderParameter.objects.filter(location_id=loc.id):
            params[p.name] = p.value

        try:
            p_class = settings.TRANSFER_PROVIDERS[loc.transfer_provider]
        except KeyError:
            # Try interpretting it as a class name ...
            p_class = loc.transfer_provider

        # FIXME - is there a better way to do this?
        parts = p_class.split('.')
        module = ''
        for p in parts[0:(len(parts) - 1)]:
            module += p
            globals()[p] = __import__(module, globals(), locals(), [], -1)
            module += '.'
        exec 'provider = ' + p_class + '(loc.name, loc.url, params)'   # noqa # pylint: disable=W0122
        return provider

    def __unicode__(self):
        return self.name


class ProviderParameter(models.Model):
    '''This class represents a "parameter" that is passed when
    instantiating a location's provider object.'''

    location = models.ForeignKey(Location)
    name = models.CharField(max_length=10)
    value = models.CharField(max_length=80, blank=True)

    class Meta:
        app_label = 'tardis_portal'
        unique_together = ('location', 'name')

    def __unicode__(self):
        return '%s: %s' % (self.name, self.value)
