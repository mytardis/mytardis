from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

from datetime import datetime

from oaipmh.common import Identify, Header, Metadata
import oaipmh.error
from oaipmh.interfaces import IOAI
from oaipmh.metadata import global_metadata_registry
from oaipmh.server import Server, oai_dc_writer

import pytz

from tardis.tardis_portal.ParameterSetManager import ParameterSetManager
from tardis.tardis_portal.creativecommonshandler import CreativeCommonsHandler
from tardis.tardis_portal.models import Experiment, ExperimentParameterSet
from tardis.tardis_portal.util import get_local_time, get_utc_time

import rifcs


class ServerImpl(IOAI):

    NS_CC = 'http://www.tardis.edu.au/schemas/creative_commons/2011/05/17'

    def __init__(self):
        global_metadata_registry.registerWriter('oai_dc', oai_dc_writer)
        global_metadata_registry.registerWriter('rif', rifcs.rifcs_writer)

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
        id_ = self._get_experiment_id(identifier)
        experiment = Experiment.objects.get(id=id_)
        header = self._get_experiment_header(experiment)
        metadata = self._get_experiment_metadata(experiment, metadataPrefix)
        about = None
        return (header, metadata, about)

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

    def listIdentifiers(self, metadataPrefix, set=None, from_=None, until=None):
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
        if set:
            # Set hierarchies are currrently not implemented
            raise oaipmh.error.NoSetHierarchyError
        experiments = self._get_experiments_in_range(from_, until)
        return map(self._get_experiment_header, experiments)

    def listMetadataFormats(self, identifier=None):
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
        if identifier:
            assert self._get_experiment_id(identifier) > 0
        return [
            ('oai_dc',
             'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
             'http://www.openarchives.org/OAI/2.0/oai_dc/'),
            ('rif', rifcs.RIFCS_SCHEMA, rifcs.RIFCS_NS)
        ]


    def listRecords(self, metadataPrefix, set=None, from_=None, until=None):
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
        if set:
            # Set hierarchies are currrently not implemented
            raise oaipmh.error.NoSetHierarchyError
        experiments = self._get_experiments_in_range(from_, until)
        def get_tuple(experiment):
            header = self._get_experiment_header(experiment)
            metadata = self._get_experiment_metadata(experiment, metadataPrefix)
            return (header, metadata, None)
        return map(get_tuple, experiments)

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

    @staticmethod
    def _get_experiment_header(experiment):
        id_ = 'experiment/%d' % experiment.id
        # Get UTC timestamp
        timestamp = get_utc_time(experiment.update_time).replace(tzinfo=None)
        return Header(id_, timestamp, [], None)

    @staticmethod
    def _get_experiments_in_range(from_, until):
        experiments = Experiment.objects.filter(public=True)
        # Filter based on boundaries provided
        if from_:
            from_ = get_local_time(from_.replace(tzinfo=pytz.utc)) # UTC->local
            experiments = experiments.filter(update_time__gte=from_)
        if until:
            until = get_local_time(until.replace(tzinfo=pytz.utc)) # UTC->local
            experiments = experiments.filter(update_time__lte=until)
        return experiments

    @staticmethod
    def _get_experiment_metadata(experiment, metadataPrefix):
        if (metadataPrefix == 'oai_dc'):
            return Metadata({
                'title': [experiment.title],
                'description': [experiment.description]
            })
        elif (metadataPrefix == 'rif'):
            cch = CreativeCommonsHandler(experiment_id=experiment.id)
            cch_psm = cch.get_or_create_cc_parameterset(False)
            return Metadata({
                'id': experiment.id,
                'title': experiment.title,
                'description': experiment.description,
                'license_name': cch_psm.get_param('license_name', True),
                'license_uri': cch_psm.get_param('license_uri', True),
            })
        else:
            raise oaipmh.error.CannotDisseminateFormatError

    @staticmethod
    def _get_experiment_id(identifier):
        try:
            type_, id_ = identifier.split('/')
            assert type_ == "experiment"
            return int(id_)
        except (AssertionError, ValueError):
            raise oaipmh.error.IdDoesNotExistError

    @classmethod
    def _get_license_uri(cls, experiment):
        return cls._get_param("license_uri", cls.NS_CC, experiment)

    @classmethod
    def _get_license_title(cls, experiment):
        return cls._get_param("license_name", cls.NS_CC, experiment)

    @classmethod
    def _get_params(self, key, namespace, experiment):
        parameterset = ExperimentParameterSet.objects.filter(
                            schema__namespace=namespace,
                            experiment__id=experiment.id)
        if len(parameterset) > 0:
            psm = ParameterSetManager(parameterset=parameterset[0])
            return psm.get_params(key, True)
        else:
            return []


def get_server():
    server = Server(ServerImpl())
    return server
