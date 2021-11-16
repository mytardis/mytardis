from abc import ABCMeta, abstractmethod

from django.conf import settings
from django.contrib.sites.requests import RequestSite
from django.test import TestCase

import oaipmh.error
import oaipmh.interfaces

import pytz

from tardis.tardis_portal.models import Experiment, License, User, \
     ExperimentParameterSet
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager
from tardis.tardis_portal.util import get_local_time

from tardis.apps.related_info.views import SCHEMA_URI

from ...provider.experiment import AbstractExperimentProvider, \
    DcExperimentProvider, RifCsExperimentProvider

def _create_test_data():
    user = User(username='testuser',
                first_name="Voltaire",
                email='voltaire@gmail.com')
    user.save()
    return (_create_experiment(user, False),
            _create_experiment(user, True), user)

def _create_experiment(user, bad):
    experiment = Experiment(title='Norwegian Blue',
                            description='Parrot + 40kV',
                            created_by=user)
    experiment.public_access = Experiment.PUBLIC_ACCESS_METADATA
    experiment.save()
    experiment.experimentauthor_set.create(order=0,
                                           author="John Cleese",
                                           url="http://nla.gov.au/nla.party-1")
    experiment.experimentauthor_set.create(order=1,
                                           author="Michael Palin",
                                           url="http://nla.gov.au/nla.party-2")
    psm = ParameterSetManager(parentObject=experiment, schema=SCHEMA_URI)
    if bad:
        params = {'type': 'website',
                  'identifier': 'https://www.badexample.com/'}
    else:
        params = {'type': 'website',
                  'identifier': 'https://www.example.com/',
                  'title': 'Google',
                  'notes': 'This is a note.'}
    for k, v in params.items():
        psm.set_param(k, v)
    return experiment

def _get_first_exp_id():
    #exp_ids = [exp.id for exp in Experiment.objects]
    #return 'experiment/%d' % min(exp_ids)
    return 'experiment/%d' % Experiment.objects.first().id

class AbstractExperimentProviderTC():
    __metaclass__ = ABCMeta

    @abstractmethod
    def _getProvider(self):
        class FakeRequest():
            def get_host(self):
                return 'example.test'
        return AbstractExperimentProvider(RequestSite(FakeRequest()))

    @abstractmethod
    def _getProviderMetadataPrefix(self):
        return ''

    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username='PUBLIC_USER_TEST')
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        self._experiment, self._experiment2, self._user = _create_test_data()

    def testIdentify(self):
        '''
        There can be only one provider that responds. This one does not.
        '''
        with self.assertRaises(NotImplementedError):
            self._getProvider().identify()()

    def testGetRecordHandlesInvalidIdentifiers(self):
        for id_ in ['experiment-1', 'MyTardis/1']:
            try:
                self._getProvider().getRecord(self._getProviderMetadataPrefix(),
                                              id_)
                self.fail("Should raise exception.")
            except oaipmh.error.IdDoesNotExistError:
                pass

    def testListIdentifiers(self):
        headers = self._getProvider() \
                      .listIdentifiers(self._getProviderMetadataPrefix())
        # Iterate through headers
        for header in headers:
            if not header.identifier().startswith('experiment'):
                continue
            e = self._experiment if header.identifier() == _get_first_exp_id() \
                else self._experiment2
            self.assertIn(str(e.id), header.identifier())
            self.assertEqual(
                header.datestamp().replace(tzinfo=pytz.utc),
                get_local_time(e.update_time))
        # Remove public flag on first experiment
        self._experiment.public_access = Experiment.PUBLIC_ACCESS_NONE
        self._experiment.save()
        headers = self._getProvider() \
            .listIdentifiers(self._getProviderMetadataPrefix())
        # First is not public, so should not appear
        self.assertEqual(len(list(headers)), 1)

    def testListIdentifiersDoesNotHandleSets(self):
        def call_with_set():
            self._getProvider() \
                .listIdentifiers(self._getProviderMetadataPrefix(),
                                 set='foo')
            with self.assertRaises(oaipmh.error.NoSetHierarchyError):
                call_with_set()

    def testListMetadataFormats(self):
        self.assertEqual(
            list(map(lambda t: t[0], self._getProvider().listMetadataFormats())),
            [self._getProviderMetadataPrefix()])

    def testListSets(self):
        try:
            self._getProvider().listSets()
            self.fail("Should throw exception.")
        except oaipmh.error.NoSetHierarchyError:
            pass

    def tearDown(self):
        pass


class DcExperimentProviderTestCase(AbstractExperimentProviderTC, TestCase):

    def _getProvider(self):
        class FakeRequest():
            def get_host(self):
                return 'example.test'
        return DcExperimentProvider(RequestSite(FakeRequest()))

    def _getProviderMetadataPrefix(self):
        return 'oai_dc'

    def testGetRecord(self):
        header, metadata, about = self._getProvider().getRecord('oai_dc', \
                                                    _get_first_exp_id())
        self.assertIn(str(self._experiment.id), header.identifier())
        self.assertEqual(
            header.datestamp().replace(tzinfo=pytz.utc),
            get_local_time(self._experiment.update_time))
        self.assertEqual(
            metadata.getField('title'), [str(self._experiment.title)])
        self.assertEqual(
            metadata.getField('description'),
            [str(self._experiment.description)])
        self.assertIsNone(about)

    def testListRecords(self):
        results = self._getProvider().listRecords('oai_dc')
        # Iterate through headers
        result_count = 0
        for header, metadata, _ in results:
            result_count += 1
            e = self._experiment if header.identifier() == _get_first_exp_id() \
                else self._experiment2
            self.assertIn(str(e.id), header.identifier())
            self.assertEqual(
                header.datestamp().replace(tzinfo=pytz.utc),
                get_local_time(e.update_time))
            self.assertEqual(
                metadata.getField('title'), [str(e.title)])
            self.assertEqual(
                metadata.getField('description'), [str(e.description)])
        # There should have been two
        self.assertEqual(result_count, 2)
        # Remove public flag on first one
        self._experiment.public_access = Experiment.PUBLIC_ACCESS_NONE
        self._experiment.save()
        headers = self._getProvider().listRecords('oai_dc')
        # First one not public, so should not appear
        self.assertEqual(len(list(headers)), 1)


class RifCsExperimentProviderTestCase(AbstractExperimentProviderTC, TestCase):

    def _getProvider(self):
        class FakeRequest():
            def get_host(self):
                return 'example.test'
        return RifCsExperimentProvider(RequestSite(FakeRequest()))

    def _getProviderMetadataPrefix(self):
        return 'rif'

    def testGetRecord(self):
        header, metadata, about = self._getProvider().getRecord('rif',
                                                     _get_first_exp_id())
        self.assertIn(str(self._experiment.id), header.identifier())
        self.assertEqual(
            header.datestamp().replace(tzinfo=pytz.utc),
            get_local_time(self._experiment.update_time))
        ns = 'http://ands.org.au/standards/rif-cs/registryObjects#relatedInfo'
        ps_id = ExperimentParameterSet.objects\
                .filter(experiment=self._experiment,schema__namespace=ns).first().id
        self.assertEqual(
            metadata.getField('id'), self._experiment.id)
        self.assertEqual(
            metadata.getField('title'), str(self._experiment.title))
        self.assertEqual(
            metadata.getField('description'),
            str(self._experiment.description))
        self.assertEqual(
            metadata.getField('licence_uri'),
            License.get_none_option_license().url)
        self.assertEqual(
            metadata.getField('licence_name'),
            License.get_none_option_license().name)
        self.assertEqual(
            list(metadata.getField('related_info')),
            [{'notes': 'This is a note.', \
                       'identifier': 'https://www.example.com/', \
                       'type': 'website', \
                       'id': ps_id, \
                       'title': 'Google'}])
        self.assertEqual(
            len(metadata.getField('collectors')), 2)
        self.assertIsNone(about)

    def testListRecords(self):
        results = self._getProvider().listRecords('rif')
        # Iterate through headers
        result_count = 0
        for header, metadata, _ in results:
            result_count += 1
            if header.identifier().startswith('experiment'):
                e = self._experiment if header.identifier() == _get_first_exp_id() \
                    else self._experiment2
                self.assertIn(str(e.id), header.identifier())
                self.assertEqual(
                    header.datestamp().replace(tzinfo=pytz.utc),
                    get_local_time(e.update_time))
                self.assertEqual(
                    metadata.getField('title'), str(e.title))
                self.assertEqual(
                    metadata.getField('description'), str(e.description))
                self.assertEqual(
                    metadata.getField('licence_uri'),
                    License.get_none_option_license().url)
                self.assertEqual(
                    metadata.getField('licence_name'),
                    License.get_none_option_license().name)
                if e == self._experiment:
                    ns = 'http://ands.org.au/standards/rif-cs/registryObjects#relatedInfo'
                    ps_id = ExperimentParameterSet.objects\
                      .filter(experiment=self._experiment,schema__namespace=ns).first().id
                    self.assertEqual(
                        list(metadata.getField('related_info')),
                        [{'notes': 'This is a note.', \
                                   'identifier': 'https://www.example.com/', \
                                   'type': 'website', \
                                   'id': ps_id, \
                                   'title': 'Google'}])
                else:
                    self.assertEqual(
                        list(metadata.getField('related_info')), [{}])
            else:
                self.assertIn(str(self._user.id), header.identifier())
                self.assertEqual(
                    header.datestamp().replace(tzinfo=pytz.utc),
                    get_local_time(self._user.last_login))
                self.assertEqual(metadata.getField('id'), self._user.id)
                self.assertEqual(
                    metadata.getField('email'), str(self._user.email))
                self.assertEqual(
                    metadata.getField('given_name'),
                    str(self._user.first_name))
                self.assertEqual(
                    metadata.getField('family_name'),
                    str(self._user.last_name))
        # There should have been two
        self.assertEqual(result_count, 2)
        # Remove public flag on first experiment
        self._experiment.public_access = Experiment.PUBLIC_ACCESS_NONE
        self._experiment.save()
        headers = self._getProvider().listRecords('rif')
        # Should now be one
        self.assertEqual(len(list(headers)), 1)

    def tearDown(self):
        pass
