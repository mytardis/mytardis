# pylint: disable=redundant-returns-doc,missing-return-type-doc,W0237
import oaipmh.error
import oaipmh.interfaces


class BaseProvider(oaipmh.interfaces.IOAI, object):
    """
    A base provider which roughly implements the PyOAI interface for OAI-PMH
    servers.

    Extend this if you're writing your own provider for a new type or a
    different metadata format.
    """

    def __init__(self, site):
        self._site = site

    def getRecord(self, metadataPrefix, identifier):
        """Get a record for a metadataPrefix and identifier.

        :param metadataPrefix: identifies metadata set to retrieve
        :type metadataPrefix: string

        :param identifier: - repository-unique identifier of record
        :type identifier: string

        :raises oaipmh.error.CannotDisseminateFormatError: if
            ``metadataPrefix`` is unknown or not supported by identifier.

        :raises oaipmh.error.IdDoesNotExistError: if identifier is
            unknown or illegal.

        :returns: a ``header``, ``metadata``, ``about`` tuple describing
            the record.
        """
        raise oaipmh.error.IdDoesNotExistError

    def identify(self):
        raise NotImplementedError

    def listIdentifiers(self, metadataPrefix, set=None, from_=None, until=None):
        """Get a list of header information on records.

        :param metadataPrefix: identifies metadata set to retrieve
        :type metadataPrefix: string

        :param set: set identifier; only return headers in set
        :type set: string

        :param from_: only retrieve headers from from_ date forward
            (in naive UTC)
        :type from_: datetime

        :param until: only retrieve headers with dates up to and including
            until date (in naive UTC)
        :type until: datetime

        :raise error.CannotDisseminateFormatError: if metadataPrefix
            is not supported by the repository.

        :raises error.NoSetHierarchyError: if the repository does not
            support sets.

        :returns: an iterable of headers.
        """
        raise oaipmh.error.CannotDisseminateFormatError

    def listMetadataFormats(self, identifier=None):
        """List metadata formats supported by repository or record.

        :param identifier: identify record for which we want to know all
                     supported metadata formats. If absent, list all metadata
                     formats supported by repository.
        :type identifier: string

        :raises error.IdDoesNotExistError: if record with
            identifier does not exist.

        :raises error.NoMetadataFormatsError: if no formats are
            available for the indicated record.

        :returns: an iterable of ``metadataPrefix``, ``schema``,
            ``metadataNamespace`` tuples (each entry in the tuple is a string).
        """
        return []

    def listRecords(self, metadataPrefix, set=None, from_=None, until=None):
        """
        Get a list of header, metadata and about information on records.

        :param metadataPrefix: identifies metadata set to retrieve
        :type metadataPrefix: string

        :param set: set identifier; only return records in set
        :type set: string

        :param from_: only retrieve records from ``from_`` date forward
                      (in naive UTC)
        :type from_: datetime

        :param until: only retrieve records with dates up to and including
                      until date (in naive UTC)
        :type until: datetime

        :raises oaipmh.error.CannotDisseminateFormatError: if ``metadataPrefix``
            is not supported by the repository.

        :raises oaipmh.error.NoSetHierarchyError: if the repository does not
            support sets.

        :returns: an iterable of ``header``, ``metadata``, ``about`` tuples.
        """
        raise oaipmh.error.CannotDisseminateFormatError

    def listSets(self):
        """
        Get a list of sets in the repository.

        :raises error.NoSetHierarchyError: if the repository does not support
            sets.

        :returns: an iterable of setSpec, setName tuples (strings).
        """
        raise oaipmh.error.NoSetHierarchyError

    def writeMetadata(self, element, metadata):
        """
        Create XML elements under the given element, using the provided
        metadata.

        Should avoid doing any model-lookups, as they should be done when
        creating the metadata.

        :param element: element to put all content under (as SubElements)
        :type element: lxml.etree.Element

        :param metadata: metadata to turn into XML
        :type metadata: oaipmh.common.Metadata

        :raises NotImplementedError: not implemented
        """
        raise NotImplementedError
