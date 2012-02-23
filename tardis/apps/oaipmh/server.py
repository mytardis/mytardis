from django.conf import settings
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

from datetime import datetime

from oaipmh.common import Identify, Header, Metadata
import oaipmh.error
from oaipmh.interfaces import IOAI
from oaipmh.metadata import MetadataRegistry
from oaipmh.server import Server, oai_dc_writer

import itertools

import pytz
from sets import Set

def _safe_import(path):
    try:
        dot = path.rindex('.')
    except ValueError:
        raise ImproperlyConfigured('%s isn\'t a middleware module' % path)
    module_, classname_ = path[:dot], path[dot + 1:]
    try:
        mod = import_module(module_)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing module %s: "%s"' %
                                   (module_, e))
    try:
        auth_class = getattr(mod, classname_)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" class' %
                                   (module_, classname_))
    auth_instance = auth_class()
    return auth_instance


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
        formats = itertools.chain(*[p.listMetadataFormats() \
                                    for p in self._providers])
        return metadata_prefix in [f[0] for f in formats]

    def readMetadata(self, metadata_prefix, element):
        raise NotImplementedError

    def writeMetadata(self, metadata_prefix, element, metadata):
        """Write metadata as XML.

        element - ElementTree element to write under
        metadata - metadata object to write
        """
        metadata['_metadata_source'].writeMetadata(element, metadata)


class ProxyingServer(IOAI):

    def __init__(self, providers):
        self.providers = providers

    def getRecord(self, metadataPrefix, identifier):
        """Get a record for a metadataPrefix and identifier.

        metadataPrefix - identifies metadata set to retrieve
        identifier - repository-unique identifier of record

        Should raise error.CannotDisseminateFormatError if
        metadataPrefix is unknown or not supported by identifier.

        Should raise error.IdDoesNotExistError if identifier is
        unknown or illegal.

        Returns a header, metadata, about tuple describing the record.
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
        """Retrieve information about the repository.

        Returns an Identify object describing the repository.
        """
        current_site = Site.objects.get_current().domain
        return Identify(
            "%s (MyTardis)" % (settings.DEFAULT_INSTITUTION,),
            'http://%s%s' % (current_site, reverse('oaipmh-endpoint')),
            '2.0',
            self._get_admin_emails(current_site),
            datetime.fromtimestamp(0),
            'no',
            'YYYY-MM-DDThh:mm:ssZ',
            []
        )

    def listIdentifiers(self, metadataPrefix, **kwargs):
        """Get a list of header information on records.

        metadataPrefix - identifies metadata set to retrieve
        set - set identifier; only return headers in set (optional)
        from_ - only retrieve headers from from_ date forward (optional)
        until - only retrieve headers with dates up to and including
                until date (optional)

        Should raise error.CannotDisseminateFormatError if metadataPrefix
        is not supported by the repository.

        Should raise error.NoSetHierarchyError if the repository does not
        support sets.

        Returns an iterable of headers.
        """
        if kwargs.has_key('set') and kwargs['set']:
            raise oaipmh.error.NoSetHierarchyError
        def appendIdents(list_, p):
            try:
                return list_ + p.listIdentifiers(metadataPrefix, **kwargs)
            except oaipmh.error.CannotDisseminateFormatError:
                return list_
        return Set(reduce(appendIdents, self.providers, []))

    def listMetadataFormats(self, **kwargs):
        """List metadata formats supported by repository or record.

        identifier - identify record for which we want to know all
                     supported metadata formats. if absent, list all metadata
                     formats supported by repository. (optional)


        Should raise error.IdDoesNotExistError if record with
        identifier does not exist.

        Should raise error.NoMetadataFormatsError if no formats are
        available for the indicated record.

        Returns an iterable of metadataPrefix, schema, metadataNamespace
        tuples (each entry in the tuple is a string).
        """
        id_known = False
        def appendFormats(list_, p):
            try:
                return list_ + p.listMetadataFormats(**kwargs)
            except oaipmh.error.IdDoesNotExistError:
                return list_
            except oaipmh.error.NoMetadataFormatsError:
                id_known = True
                return list_
        formats = Set(reduce(appendFormats, self.providers, []))
        if kwargs.has_key('identifier'):
            if len(formats) == 0:
                if id_known:
                    raise oaipmh.error.NoMetadataFormatsError
                else:
                    raise oaipmh.error.IdDoesNotExistError
        return formats

    def listRecords(self, metadataPrefix, **kwargs):
        """Get a list of header, metadata and about information on records.

        metadataPrefix - identifies metadata set to retrieve
        set - set identifier; only return records in set (optional)
        from_ - only retrieve records from from_ date forward (optional)
        until - only retrieve records with dates up to and including
                until date (optional)

        Should raise error.CannotDisseminateFormatError if metadataPrefix
        is not supported by the repository.

        Should raise error.NoSetHierarchyError if the repository does not
        support sets.

        Returns an iterable of header, metadata, about tuples.
        """
        if kwargs.has_key('set') and kwargs['set']:
            raise oaipmh.error.NoSetHierarchyError
        if metadataPrefix not in [f[0] for f in self.listMetadataFormats()]:
            raise oaipmh.error.CannotDisseminateFormatError
        def appendRecords(list_, p):
            try:
                return list_ + p.listRecords(metadataPrefix, **kwargs)
            except oaipmh.error.CannotDisseminateFormatError:
                return list_
        return Set(reduce(appendRecords, self.providers, []))

    def listSets(self):
        """Get a list of sets in the repository.

        Should raise error.NoSetHierarchyError if the repository does not
        support sets.

        Returns an iterable of setSpec, setName tuples (strings).
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
        elif settings.ADMINS:
            # Otherwise we should have a host email
            return map(lambda t: t[1], list(settings.ADMINS))
        elif settings.EMAIL_HOST_USER:
            # Otherwise we should have a host email
            return [settings.EMAIL_HOST_USER]
        # We might as well advertise our ignorance
        return ['noreply@'+current_site]


def get_server():
    providers = [_safe_import(p) for p in settings.OAIPMH_PROVIDERS]
    server = Server(ProxyingServer(providers),
                    metadata_registry=ProxyingMetadataRegistry(providers))
    return server
