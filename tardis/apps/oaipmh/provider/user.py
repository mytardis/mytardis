from django.conf import settings
from lxml.etree import SubElement

from oaipmh.common import Identify, Header, Metadata
import oaipmh.error
from oaipmh.interfaces import IOAI
from oaipmh.metadata import global_metadata_registry
from oaipmh.server import Server, oai_dc_writer, NS_XSI

import pytz

from tardis.tardis_portal.models import User, Experiment
from tardis.tardis_portal.util import get_local_time, get_utc_time

from .base import BaseProvider

class RifCsUserProvider(BaseProvider):

    RIFCS_NS = 'http://ands.org.au/standards/rif-cs/registryObjects'
    RIFCS_SCHEMA = \
    'http://services.ands.org.au/documentation/rifcs/schema/registryObjects.xsd'

    def getRecord(self, metadataPrefix, identifier):
        """
        Return record if we handle it.
        """
        # This should raise IdDoesNotExistError if not an experiment
        id_ = self._get_id_from_identifier(identifier)
        # Don't process requests unless we handle this prefix
        if not self._handles_metadata_prefix(metadataPrefix):
            raise oaipmh.error.CannotDisseminateFormatError
        user = User.objects.get(id=id_)
        header = self._get_header(user)
        metadata = self._get_metadata(user, metadataPrefix)
        about = None
        return (header, metadata, about)

    def listIdentifiers(self, metadataPrefix, set=None, from_=None, until=None):
        """
        Return identifiers in range, provided we handle this metadata prefix.
        """
        # Set hierarchies are currrently not implemented
        if set:
            raise oaipmh.error.NoSetHierarchyError
        # Don't process requests unless we handle this prefix
        if not self._handles_metadata_prefix(metadataPrefix):
            raise oaipmh.error.CannotDisseminateFormatError
        experiments = self._get_in_range(from_, until)
        return map(self._get_header, experiments)

    def listRecords(self, metadataPrefix, set=None, from_=None, until=None):
        """
        Return records in range, provided we handle this metadata prefix.
        """
        # Set hierarchies are currrently not implemented
        if set:
            raise oaipmh.error.NoSetHierarchyError
        # Don't process requests unless we handle this prefix
        if not self._handles_metadata_prefix(metadataPrefix):
            raise oaipmh.error.CannotDisseminateFormatError
        experiments = self._get_in_range(from_, until)
        def get_tuple(experiment):
            header = self._get_header(experiment)
            metadata = self._get_metadata(experiment, metadataPrefix)
            return (header, metadata, None)
        return map(get_tuple, experiments)

    def listSets(self):
        """
        No support for sets.
        """
        raise oaipmh.error.NoSetHierarchyError

    def listMetadataFormats(self, identifier=None):
        """
        Return metadata format if no identifier, or identifier
        is a valid experiment.
        """
        try:
            if identifier != None:
                self._get_id_from_identifier(identifier)
            return [('rif', self.RIFCS_SCHEMA, self.RIFCS_NS)]
        except oaipmh.error.IdDoesNotExistError:
            return []

    @staticmethod
    def get_id(user):
        return 'user/%d' % user.id

    @staticmethod
    def _get_id_from_identifier(identifier):
        try:
            type_, id_ = identifier.split('/')
            assert type_ == "user"
            return int(id_)
        except (AssertionError, ValueError):
            raise oaipmh.error.IdDoesNotExistError

    def _get_header(self, user):
        # Get UTC timestamp
        # Use of "last_login" is not ideal, but should work well enough for now.
        timestamp = get_utc_time(user.last_login).replace(tzinfo=None)
        return Header(self.get_id(user), timestamp, [], None)

    @staticmethod
    def _get_in_range(from_, until):
        users = User.objects.exclude(experiment__public_access=Experiment.PUBLIC_ACCESS_NONE)
        # Filter based on boundaries provided
        # Use of "last_login" is not ideal, but should work well enough for now.
        if from_:
            from_ = get_local_time(from_.replace(tzinfo=pytz.utc)) # UTC->local
            users = users.filter(last_login__gte=from_)
        if until:
            until = get_local_time(until.replace(tzinfo=pytz.utc)) # UTC->local
            users = users.filter(last_login__lte=until)

        return users

    def _get_metadata(self, user, metadataPrefix):
        collected_experiments = \
            Experiment.objects.filter(created_by=user) \
                        .exclude(public_access=Experiment.PUBLIC_ACCESS_NONE)
        owns_experiments = Experiment.safe.owned_by_user_id(user.id)\
                                          .exclude(public_access=Experiment.PUBLIC_ACCESS_NONE)
        return Metadata({
            '_metadata_source': self,
            'id': user.id,
            'email': user.email,
            'given_name': user.first_name,
            'family_name': user.last_name,
            'collected_experiments': collected_experiments,
            'owns_experiments': owns_experiments,
        })

    def _handles_metadata_prefix(self, metadataPrefix):
        return metadataPrefix == 'rif'

    @staticmethod
    def get_rifcs_id(id_, site_= None):
        return "%s/user/%s" % (getattr(settings,
                                       'RIFCS_KEY',
                                       site_.domain),
                               id_)

    def writeMetadata(self, element, metadata):
        from .experiment import RifCsExperimentProvider
        def _nsrif(name):
            return '{%s}%s' % (self.RIFCS_NS, name)
        def _get_id(metadata):
            return self.get_rifcs_id(metadata.getMap().get('id'), self._site)
        def _get_group(metadata):
            return metadata.getMap().get('group', getattr(settings,
                                                          'RIFCS_GROUP', ''))
        def _get_originating_source(metadata):
            # TODO: Handle repository data from federated MyTardis instances
            return "http://%s/" % self._site.domain
        # registryObjects
        wrapper = SubElement(element, _nsrif('registryObjects'), \
                       nsmap={None: self.RIFCS_NS, 'xsi': NS_XSI} )
        wrapper.set('{%s}schemaLocation' % NS_XSI,
                    '%s %s' % (self.RIFCS_NS, self.RIFCS_SCHEMA))
        # registryObject
        obj = SubElement(wrapper, _nsrif('registryObject') )
        obj.set('group', _get_group(metadata))
        # key
        SubElement(obj, _nsrif('key')).text = _get_id(metadata)
        # originatingSource
        SubElement(obj, _nsrif('originatingSource')).text = \
            _get_originating_source(metadata)
        # collection
        collection = SubElement(obj, _nsrif('party') )
        collection.set('type', 'person')
        # name
        name = SubElement(collection, _nsrif('name') )
        name.set('type', 'primary')
        namePartMap = {'given': metadata.getMap().get('given_name'),
                       'family': metadata.getMap().get('family_name')}
        for k,v in namePartMap.items():
            namePart = SubElement(name, _nsrif('namePart'))
            namePart.set('type', k)
            namePart.text = v
        # location
        electronic = SubElement(SubElement(SubElement(collection,
                                                      _nsrif('location') ),
                                           _nsrif('address')),
                                _nsrif('electronic'))
        electronic.set('type', 'email')
        electronic.text = metadata.getMap().get('email')
        for experiment in metadata.getMap().get('collected_experiments'):
            relatedObject = SubElement(collection, _nsrif('relatedObject') )
            SubElement(relatedObject, _nsrif('key')).text = \
                RifCsExperimentProvider.get_rifcs_id(experiment.id, self._site)
            SubElement(relatedObject, _nsrif('relation')) \
                .set('type', 'isCollectorOf')
        for experiment in metadata.getMap().get('owns_experiments'):
            relatedObject = SubElement(collection, _nsrif('relatedObject') )
            SubElement(relatedObject, _nsrif('key')).text = \
                RifCsExperimentProvider.get_rifcs_id(experiment.id, self._site)
            SubElement(relatedObject, _nsrif('relation')) \
                .set('type', 'isManagerOf')



