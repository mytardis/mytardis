from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

from datetime import datetime

from oaipmh.common import Identify
from oaipmh.interfaces import IOAI
from oaipmh.server import Server

class ServerImpl(IOAI):

    @staticmethod
    def getRecord(metadataPrefix, identifier):
        """Get a record for a metadataPrefix and identifier.

        metadataPrefix - identifies metadata set to retrieve
        identifier - repository-unique identifier of record

        Should raise error.CannotDisseminateFormatError if
        metadataPrefix is unknown or not supported by identifier.

        Should raise error.IdDoesNotExistError if identifier is
        unknown or illegal.

        Returns a header, metadata, about tuple describing the record.
        """
        raise NotImplementedError

    @staticmethod
    def identify():
        """Retrieve information about the repository.

        Returns an Identify object describing the repository.
        """
        current_site = Site.objects.get_current().domain
        return Identify(
            "Repo Name",
            'http://%s%s' % (current_site, reverse('oaipmh-endpoint')),
            '2.0',
            ['user@domain.com'], # TODO: Use a real value
            datetime.fromtimestamp(0),
            'no',
            'YYYY-MM-DDThh:mm:ssZ',
            []
        )

    @staticmethod
    def listIdentifiers(metadataPrefix, set=None, from_=None, until=None):
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
        raise NotImplementedError

    @staticmethod
    def listMetadataFormats(identifier=None):
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
        raise NotImplementedError

    @staticmethod
    def listRecords(metadataPrefix, set=None, from_=None, until=None):
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
        raise NotImplementedError

    @staticmethod
    def listSets():
        """Get a list of sets in the repository.

        Should raise error.NoSetHierarchyError if the repository does not
        support sets.

        Returns an iterable of setSpec, setName tuples (strings).
        """
        raise NotImplementedError


def get_server():
    server = Server(ServerImpl())
    return server
