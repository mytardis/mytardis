import itertools
from datetime import datetime
from functools import reduce
from importlib import import_module

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

import oaipmh.error
from oaipmh.common import Identify
from oaipmh.interfaces import IOAI
from oaipmh.metadata import MetadataRegistry
from oaipmh.server import Server


def _safe_import_class(path):
    try:
        dot = path.rindex('.')
    except ValueError:
        raise ImproperlyConfigured('%s isn\'t a middleware module' % path)
    module_, classname_ = path[:dot], path[dot + 1:]
    try:
        mod = import_module(module_)
    except ImportError as e:
        raise ImproperlyConfigured('Error importing module %s: "%s"' %
                                   (module_, e))
    try:
        auth_class = getattr(mod, classname_)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" class' %
                                   (module_, classname_))
    return auth_class


class ProxyingMetadataRegistry(MetadataRegistry):
    """
    A registry that only writes, and does so by proxying to Providers.
    """
    def __init__(self, providers):
        self._providers = providers

    def registerReader(self, metadata_prefix, reader):
        raise NotImplementedError

    def registerWriter(self, metadata_prefix, writer):
        raise NotImplementedError

    def hasReader(self, metadata_prefix):
        return False

    def hasWriter(self, metadata_prefix):
        formats = itertools.chain(*[p.listMetadataFormats()
                                    for p in self._providers])
        return metadata_prefix in [f[0] for f in formats]

    def readMetadata(self, metadata_prefix, element):
        raise NotImplementedError

    def writeMetadata(self, metadata_prefix, element, metadata):
        """Write metadata as XML.

        element - ElementTree element to write under
        metadata - metadata object to write
        """
        metadata['_writeMetadata'](element, metadata)


class ProxyingServer(IOAI):

    def __init__(self, providers):
        self.providers = providers

    def getRecord(self, metadataPrefix, identifier):
        """
        Get a record for a metadataPrefix and identifier.

        :raises oaipmh.error.CannotDisseminateFormatError: if no provider
            returns a result, but at least one provider
            responds with :py:exc:`oaipmh.error.CannotDisseminateFormatError`
            (meaning the identifier exists)
        :raises oaipmh.error.IdDoesNotExistError: if all providers fail with
            :py:exc:`oaipmh.error.IdDoesNotExistError`

        :returns: first successful provider response
        :rtype: response
        """
        id_exists = False
        # Try the providers until we succeed
        for p in self.providers:
            try:
                result = p.getRecord(metadataPrefix, identifier)
                return result
            except oaipmh.error.CannotDisseminateFormatError:
                id_exists = True
            except oaipmh.error.IdDoesNotExistError:
                pass
        # If we fail, respond sensibly
        if id_exists:
            raise oaipmh.error.CannotDisseminateFormatError
        raise oaipmh.error.IdDoesNotExistError

    def identify(self):
        """
        Retrieve information about the repository.

        :returns: an :py:class:`oaipmh.common.Identify` object describing the
            repository.
        :rtype: oaipmh.common.Identify
        """
        current_site = Site.objects.get_current().domain
        if getattr(settings, 'CSRF_COOKIE_SECURE', False):
            protocol = 'https'
        else:
            protocol = 'http'
        return Identify(
            "%s (MyTardis)" % (settings.DEFAULT_INSTITUTION,),
            '%s://%s%s' % (protocol, current_site,
                           reverse('oaipmh-endpoint')),
            '2.0',
            self._get_admin_emails(current_site),
            datetime.fromtimestamp(0),
            'no',
            'YYYY-MM-DDThh:mm:ssZ',
            []
        )

    def listIdentifiers(self, metadataPrefix, **kwargs):
        """
        Lists identifiers from all providers as a single set.

        :raises error.CannotDisseminateFormatError: if ``metadataPrefix``
            is not supported by the repository.

        :raises error.NoSetHierarchyError: if a set is provided, as the
            repository does not support sets.

        :returns: a :py:class:`set.Set` of headers.
        :rtype: set
        """
        if 'set' in kwargs and kwargs['set']:
            raise oaipmh.error.NoSetHierarchyError
        if metadataPrefix not in [f[0] for f in self.listMetadataFormats()]:
            raise oaipmh.error.CannotDisseminateFormatError

        def appendIdents(list_, p):
            try:
                return list_ + list(p.listIdentifiers(metadataPrefix, **kwargs))
            except oaipmh.error.CannotDisseminateFormatError:
                return list_
        return frozenset(reduce(appendIdents, self.providers, []))

    # pylint: disable=W0222
    def listMetadataFormats(self, **kwargs):
        """
        List metadata formats from all providers in a single set.

        :raises error.IdDoesNotExistError: if record with
            identifier does not exist.

        :raises error.NoMetadataFormatsError: if no formats are
            available for the indicated record, but it does exist.

        :returns: a `frozenset` of ``metadataPrefix``, ``schema``,
            ``metadataNamespace`` tuples (each entry in the tuple is a string).
        :rtype: frozenset
        """
        def appendFormats(list_, p):
            try:
                return list_ + p.listMetadataFormats(**kwargs)
            except oaipmh.error.IdDoesNotExistError:
                return list_
            except oaipmh.error.NoMetadataFormatsError:
                return list_
        formats = frozenset(reduce(appendFormats, self.providers, []))
        if 'identifier' in kwargs:
            if not formats:
                raise oaipmh.error.IdDoesNotExistError
        return formats

    def listRecords(self, metadataPrefix, **kwargs):
        """
        Lists records from all providers as a single set.

        :raises error.CannotDisseminateFormatError: if ``metadataPrefix``
            is not supported by the repository.

        :raises error.NoSetHierarchyError: if a set is provided, as the
            repository does not support sets.

        :returns: a :py:class:`set.Set` of ``header``, ``metadata``, ``about``
            tuples.
        :rtype: set
        """
        if 'set' in kwargs and kwargs['set']:
            raise oaipmh.error.NoSetHierarchyError
        if metadataPrefix not in [f[0] for f in self.listMetadataFormats()]:
            raise oaipmh.error.CannotDisseminateFormatError

        def appendRecords(list_, p):
            try:
                return list_ + list(p.listRecords(metadataPrefix, **kwargs))
            except oaipmh.error.CannotDisseminateFormatError:
                return list_
        return frozenset(reduce(appendRecords, self.providers, []))

    def listSets(self):
        """
        List sets.

        :raises oaipmh.error.NoSetHierarchyError: because set hierarchies are
            currrently not implemented
        """
        # Set hierarchies are currrently not implemented
        raise oaipmh.error.NoSetHierarchyError

    def _get_admin_emails(self, current_site):
        '''
        Checks all the sources we might have for administrator email addresses
        and returns first available.
        '''
        # Get admin users from user database
        admin_users = User.objects.filter(is_superuser=True)
        if admin_users:
            # Use admin user email addresses if we have them
            return map(lambda u: u.email, admin_users)
        if settings.ADMINS:
            # Otherwise we should have a host email
            return map(lambda t: t[1], list(settings.ADMINS))
        if settings.EMAIL_HOST_USER:
            # Otherwise we should have a host email
            return [settings.EMAIL_HOST_USER]
        # We might as well advertise our ignorance
        return ['noreply@'+current_site]

_servers = {}


def get_server(current_site):
    # Lookup for existing server first
    if current_site.domain in _servers:
        return _servers[current_site.domain]

    def create_provider(provider_name):
        class_ = _safe_import_class(provider_name)
        return class_(current_site)
    # Create new objects with site argument
    providers = [create_provider(p) for p in settings.OAIPMH_PROVIDERS]
    server = Server(ProxyingServer(providers),
                    metadata_registry=ProxyingMetadataRegistry(providers))
    # Memoize
    _servers[current_site.domain] = server
    return server
