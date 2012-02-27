from abc import abstractmethod

from django.conf import settings
from django.core.urlresolvers import reverse
from lxml.etree import SubElement

from oaipmh.common import Identify, Header, Metadata
import oaipmh.error
from oaipmh.interfaces import IOAI
from oaipmh.metadata import global_metadata_registry
from oaipmh.server import Server, oai_dc_writer, NS_XSI

import pytz

from tardis.tardis_portal.creativecommonshandler import CreativeCommonsHandler
from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.util import get_local_time, get_utc_time

from .base import BaseProvider

class AbstractExperimentProvider(BaseProvider):

    NS_CC = 'http://www.tardis.edu.au/schemas/creative_commons/2011/05/17'

    def getRecord(self, metadataPrefix, identifier):
        """
        Return record if we handle it.
        """
        # This should raise IdDoesNotExistError if not an experiment
        id_ = self._get_id_from_identifier(identifier)
        # Don't process requests unless we handle this prefix
        if not self._handles_metadata_prefix(metadataPrefix):
            raise oaipmh.error.CannotDisseminateFormatError
        experiment = Experiment.objects.get(id=id_)
        header = self._get_header(experiment)
        metadata = self._get_metadata(experiment, metadataPrefix)
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

    @staticmethod
    def get_id(experiment):
        return 'experiment/%d' % experiment.id

    @staticmethod
    def _get_id_from_identifier(identifier):
        try:
            type_, id_ = identifier.split('/')
            assert type_ == "experiment"
            return int(id_)
        except (AssertionError, ValueError):
            raise oaipmh.error.IdDoesNotExistError

    def _get_header(self, experiment):
        # Get UTC timestamp
        timestamp = get_utc_time(experiment.update_time).replace(tzinfo=None)
        return Header(self.get_id(experiment), timestamp, [], None)

    @abstractmethod
    def _get_metadata(self):
        pass

    @staticmethod
    def _get_in_range(from_, until):
        experiments = Experiment.objects.filter(public=True)
        # Filter based on boundaries provided
        if from_:
            from_ = get_local_time(from_.replace(tzinfo=pytz.utc)) # UTC->local
            experiments = experiments.filter(update_time__gte=from_)
        if until:
            until = get_local_time(until.replace(tzinfo=pytz.utc)) # UTC->local
            experiments = experiments.filter(update_time__lte=until)
        return experiments

    @abstractmethod
    def _handles_metadata_prefix(self):
        return False

    def writeMetadata(self, element, metadata):
        oai_dc_writer(element, metadata)


class DcExperimentProvider(AbstractExperimentProvider):

    def listMetadataFormats(self, identifier=None):
        """
        Return metadata format if no identifier, or identifier
        is a valid experiment.
        """
        try:
            if identifier != None:
                self._get_id_from_identifier(identifier)
            return [
                ('oai_dc',
                 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
                 'http://www.openarchives.org/OAI/2.0/oai_dc/')
            ]
        except oaipmh.error.IdDoesNotExistError:
            return []

    def _get_metadata(self, experiment, metadataPrefix):
        return Metadata({
            '_metadata_source': self,
            'title': [experiment.title],
            'description': [experiment.description],
        })

    def _handles_metadata_prefix(self, metadataPrefix):
        return metadataPrefix == 'oai_dc'



class RifCsExperimentProvider(AbstractExperimentProvider):

    RIFCS_NS = 'http://ands.org.au/standards/rif-cs/registryObjects'
    RIFCS_SCHEMA = \
    'http://services.ands.org.au/documentation/rifcs/schema/registryObjects.xsd'

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

    def _get_metadata(self, experiment, metadataPrefix):
        cch = CreativeCommonsHandler(experiment_id=experiment.id)
        cch_psm = cch.get_or_create_cc_parameterset(False)
        return Metadata({
            '_metadata_source': self,
            'id': experiment.id,
            'title': experiment.title,
            'description': experiment.description,
            # Note: Property names are US-spelling, but RIF-CS is Australian
            'licence_name': cch_psm.get_param('license_name', True),
            'licence_uri': cch_psm.get_param('license_uri', True),
            'owner': experiment.created_by
        })

    def _handles_metadata_prefix(self, metadataPrefix):
        return metadataPrefix == 'rif'

    @staticmethod
    def get_rifcs_id(id_, site_=None):
        return "%s/experiment/%s" % (getattr(settings, 'RIFCS_KEY',
                                             site_.domain),
                                     id_)

    def writeMetadata(self, element, metadata):
        from .user import RifCsUserProvider
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
        def _get_location(metadata):
            return "http://%s%s" % \
                ( self._site.domain,
                  reverse('experiment', args=[metadata.getMap().get('id')]) )
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
        collection = SubElement(obj, _nsrif('collection') )
        collection.set('type', 'dataset')
        # name
        name = SubElement(collection, _nsrif('name') )
        name.set('type', 'primary')
        SubElement(name, _nsrif('namePart')).text = metadata.getMap().get('title')
        # description
        description = SubElement(collection, _nsrif('description') )
        description.set('type', 'brief')
        description.text = metadata.getMap().get('description')
        # location
        electronic = SubElement(SubElement(SubElement(collection,
                                                      _nsrif('location') ),
                                           _nsrif('address')),
                                _nsrif('electronic'))
        electronic.set('type', 'url')
        electronic.text = _get_location(metadata)
        # rights
        rights = SubElement(collection, _nsrif('rights') )
        licence_ = SubElement(rights, _nsrif('licence') )
        licence_.set('rightsUri', metadata.getMap().get('licence_uri'))
        licence_.text = metadata.getMap().get('licence_name')
        # related object - owner
        relatedObject = SubElement(collection, _nsrif('relatedObject') )
        SubElement(relatedObject, _nsrif('key')).text = \
            RifCsUserProvider.get_rifcs_id(metadata.getMap().get('owner').id,
                                           self._site)
        SubElement(relatedObject, _nsrif('relation')) \
            .set('type', 'hasCollector')




