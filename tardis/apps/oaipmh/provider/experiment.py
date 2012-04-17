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

from tardis.tardis_portal.models import Experiment, License, User
from tardis.tardis_portal.util import get_local_time, get_utc_time

from .base import BaseProvider

class AbstractExperimentProvider(BaseProvider):

    NS_CC = 'http://www.tardis.edu.au/schemas/creative_commons/2011/05/17'

    def getRecord(self, metadataPrefix, identifier):
        """
        Return record if we handle it.
        """
        # This should raise IdDoesNotExistError if not an experiment
        type_, id_ = self._get_id_from_identifier(identifier)
        # Don't process requests unless we handle this prefix
        if not self._handles_metadata_prefix(metadataPrefix):
            raise oaipmh.error.CannotDisseminateFormatError
        if type_ == 'experiment':
            obj = Experiment.objects.get(id=id_)
        else:
            obj = User.objects.get(id=id_)
        metadata = self._get_metadata(obj, metadataPrefix)
        header = self._get_header(obj)
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
        objects = self._get_in_range(from_, until)
        print str(objects)
        return map(self._get_header, objects)

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
        objects = self._get_in_range(from_, until)
        def get_tuple(obj):
            header = self._get_header(obj)
            metadata = self._get_metadata(obj, metadataPrefix)
            return (header, metadata, None)
        return map(get_tuple, objects)

    def listSets(self):
        """
        No support for sets.
        """
        raise oaipmh.error.NoSetHierarchyError

    @staticmethod
    def get_id(obj):
        if (isinstance(obj, User)):
            return 'user/%d' % obj.id
        else:
            return 'experiment/%d' % obj.id

    def _get_id_from_identifier(self, identifier):
        return self._split_type_and_id(identifier, ["experiment", "user"])

    def _split_type_and_id(self, identifier, allowed_types):
        try:
            type_, id_ = identifier.split('/')
            assert type_ in allowed_types
            return (type_, int(id_))
        except (AssertionError, ValueError):
            raise oaipmh.error.IdDoesNotExistError

    def _get_header(self, obj):
        if (isinstance(obj, User)):
            timeFunc = lambda u: u.last_login
        else:
            timeFunc = lambda e: e.update_time
        # Get UTC timestamp
        timestamp = get_utc_time(timeFunc(obj)).replace(tzinfo=None)
        return Header(self.get_id(obj), timestamp, [], None)

    def _get_metadata(self, obj, metadataPrefix):
        if (isinstance(obj, User)):
            return self._get_user_metadata(obj, metadataPrefix)
        else:
            return self._get_experiment_metadata(obj, metadataPrefix)

    @abstractmethod
    def _get_experiment_metadata(self):
        raise NotImplementedError

    @abstractmethod
    def _get_user_metadata(self):
        raise NotImplementedError

    def _get_in_range(self, from_, until):
        from itertools import chain
        from sets import Set
        experiments = Experiment.objects\
            .select_related('created_by')\
            .exclude(public_access=Experiment.PUBLIC_ACCESS_NONE)\
            .exclude(description='')
        # Filter based on boundaries provided
        if from_:
            from_ = get_local_time(from_.replace(tzinfo=pytz.utc)) # UTC->local
            experiments = experiments.filter(update_time__gte=from_)
        if until:
            until = get_local_time(until.replace(tzinfo=pytz.utc)) # UTC->local
            experiments = experiments.filter(update_time__lte=until)
        def get_users_from_experiment(experiment):
            return filter(lambda u: u.get_profile().isValidPublicContact(),
                          chain([experiment.created_by],
                                experiment.get_owners()))
        users = chain(map(get_users_from_experiment, experiments))
        return Set(chain(experiments, *users))

    @abstractmethod
    def _handles_metadata_prefix(self):
        return False


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

    def _get_in_range(self, from_, until):
        return filter(lambda obj: isinstance(obj, Experiment),
                      super(DcExperimentProvider, self)\
                        ._get_in_range(from_, until))

    def _get_id_from_identifier(self, identifier):
        return self._split_type_and_id(identifier, ["experiment"])

    def _get_experiment_metadata(self, experiment, metadataPrefix):
        return Metadata({
            '_writeMetadata': lambda e, m: oai_dc_writer(e, m),
            'title': [experiment.title],
            'description': [experiment.description],
        })

    def _get_user_metadata(self):
        raise None

    def _handles_metadata_prefix(self, metadataPrefix):
        return metadataPrefix == 'oai_dc'



class RifCsExperimentProvider(AbstractExperimentProvider):

    def listMetadataFormats(self, identifier=None):
        """
        Return metadata format if no identifier, or identifier
        is a valid experiment.
        """
        from . import RIFCS_NS, RIFCS_SCHEMA
        try:
            if identifier != None:
                self._get_id_from_identifier(identifier)
            return [('rif', RIFCS_SCHEMA, RIFCS_NS)]
        except oaipmh.error.IdDoesNotExistError:
            return []

    def _get_experiment_metadata(self, experiment, metadataPrefix):
        license_ = experiment.license or License.get_none_option_license()
        # Access Rights statement
        if experiment.public_access == Experiment.PUBLIC_ACCESS_METADATA:
            access = "Only metadata is publicly available online."+\
                    " Requests for further access should be directed to a"+\
                    " listed data manager."
        else:
            access = "All data is publicly available online."
        return Metadata({
            '_writeMetadata': self._get_experiment_writer_func(),
            'id': experiment.id,
            'title': experiment.title,
            'description': experiment.description,
            # Note: Property names are US-spelling, but RIF-CS is Australian
            'licence_name': license_.name,
            'licence_uri': license_.url,
            'access': access,
            'collectors': [experiment.created_by],
            'managers': experiment.get_owners()
        })

    def _get_user_metadata(self, user, metadataPrefix):
        collected_experiments = \
            Experiment.objects.filter(created_by=user) \
                        .exclude(public_access=Experiment.PUBLIC_ACCESS_NONE)
        owns_experiments = Experiment.safe.owned_by_user_id(user.id)\
                                          .exclude(public_access=Experiment.PUBLIC_ACCESS_NONE)
        return Metadata({
            '_writeMetadata': self._get_user_writer_func(),
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
    def get_rifcs_id(id_, site_=None):
        return "%s/experiment/%s" % (getattr(settings, 'RIFCS_KEY',
                                             site_.domain),
                                     id_)

    def _get_experiment_writer_func(self):
        '''
        Create function which will write experiment metadata.
        '''
        from functools import partial
        return partial(self.writeExperimentMetadata,
                       site=self._site,
                       writer=self.ExperimentWriter)

    @staticmethod
    def writeExperimentMetadata(element, metadata, site=None, writer=None):
        '''
        Wrapper around experiment writer.
        '''
        writer(element, metadata, site).write()

    class ExperimentWriter:

        def __init__(self, root, metadata, site):
            self.root = root
            self.metadata = metadata
            self.site = site

        @staticmethod
        def _nsrif(name):
            from . import RIFCS_NS
            return '{%s}%s' % (RIFCS_NS, name)



        def write(self):
            # Get our data
            metadata, site = (self.metadata, self.site)
            _nsrif = self._nsrif
            def _get_id(metadata):
                return RifCsExperimentProvider.get_rifcs_id(metadata.getMap().get('id'), site)
            def _get_group(metadata):
                return getattr(settings, 'RIFCS_GROUP', '')
            def _get_originating_source(metadata):
                # TODO: Handle repository data from federated MyTardis instances
                return "http://%s/" % site.domain
            def _get_location(metadata):
                return "http://%s%s" % \
                    ( site.domain,
                      reverse('experiment', args=[metadata.getMap().get('id')]) )
            # registryObjects
            wrapper = self.writeRegistryObjectsWrapper()
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
            SubElement(name, _nsrif('namePart')).text = \
                                                    metadata.getMap().get('title')
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
            access = SubElement(rights, _nsrif('accessRights') )
            access.text = metadata.getMap().get('access')
            licence_ = SubElement(rights, _nsrif('licence') )
            licence_.set('rightsUri', metadata.getMap().get('licence_uri'))
            licence_.text = metadata.getMap().get('licence_name')
            # related object - collectors
            managers = list(metadata.getMap().get('managers'))
            for collector in metadata.getMap().get('collectors'):
                relationships = ['hasCollector']
                if collector in managers:
                    relationships.append('isManagedBy')
                    managers.remove(collector)
                self.writeRelatedObject(collection, collector, relationships)
            # related object - managers
            for manager in managers:
                self.writeRelatedObject(collection, manager, ['isManagedBy'])

        def writeRegistryObjectsWrapper(self, ):
            # <registryObjects
            #    xsi:schemaLocation="
            #        http://ands.org.au/standards/rif-cs/registryObjects
            #        http://services.ands.org.au/documentation/rifcs/schema/registryObjects.xsd"
            #    xmlns="http://ands.org.au/standards/rif-cs/registryObjects">
            from . import RIFCS_NS, RIFCS_SCHEMA
            wrapper = SubElement(self.root, self._nsrif('registryObjects'), \
                           nsmap={None: RIFCS_NS, 'xsi': NS_XSI} )
            wrapper.set('{%s}schemaLocation' % NS_XSI,
                        '%s %s' % (RIFCS_NS, RIFCS_SCHEMA))
            return wrapper

        def writeRelatedObject(self, element, obj, relationsTypes):
            # <relatedObject>
            #     <key>user/1</key>
            #     <relation type="isManagedBy"/>
            # </relatedObjexperimentect>
            def get_user_rifcs_id(identifier, site):
                return "%s/user/%s" % (getattr(settings,
                                           'RIFCS_KEY',
                                           site.domain),
                                           identifier)
            if not obj.get_profile().isValidPublicContact():
                return
            relatedObject = SubElement(element, self._nsrif('relatedObject') )
            SubElement(relatedObject, self._nsrif('key')).text = \
                get_user_rifcs_id(obj.id, self.site)
            for relation in relationsTypes:
                SubElement(relatedObject, self._nsrif('relation')) \
                    .set('type', relation)

    def _get_user_writer_func(self):
        from functools import partial
        return partial(self.writeUserMetadata, site=self._site)

    @staticmethod
    def writeUserMetadata(element, metadata, site=None):
        from . import RIFCS_NS, RIFCS_SCHEMA
        def _nsrif(name):
            return '{%s}%s' % (RIFCS_NS, name)
        def _get_id(metadata):
            return "%s/user/%s" % (getattr(settings,
                                           'RIFCS_KEY',
                                           site.domain),
                                   metadata.getMap().get('id'))
        def _get_group(metadata):
            return metadata.getMap().get('group', getattr(settings,
                                                          'RIFCS_GROUP', ''))
        def _get_originating_source(metadata):
            # TODO: Handle repository data from federated MyTardis instances
            return "http://%s/" % site.domain
        # registryObjects
        wrapper = SubElement(element, _nsrif('registryObjects'), \
                       nsmap={None: RIFCS_NS, 'xsi': NS_XSI} )
        wrapper.set('{%s}schemaLocation' % NS_XSI,
                    '%s %s' % (RIFCS_NS, RIFCS_SCHEMA))
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
            if v == '': # Exclude empty parts
                continue
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

        owns_experiments = list(metadata.getMap().get('owns_experiments'))
        for experiment in metadata.getMap().get('collected_experiments'):
            relatedObject = SubElement(collection, _nsrif('relatedObject') )
            SubElement(relatedObject, _nsrif('key')).text = \
                RifCsExperimentProvider.get_rifcs_id(experiment.id, site)
            SubElement(relatedObject, _nsrif('relation')) \
                .set('type', 'isCollectorOf')
            if experiment in owns_experiments:
                SubElement(relatedObject, _nsrif('relation')) \
                    .set('type', 'isManagerOf')
                owns_experiments.remove(experiment)
        for experiment in owns_experiments:
            relatedObject = SubElement(collection, _nsrif('relatedObject') )
            SubElement(relatedObject, _nsrif('key')).text = \
                RifCsExperimentProvider.get_rifcs_id(experiment.id, site)
            SubElement(relatedObject, _nsrif('relation')) \
                .set('type', 'isManagerOf')








