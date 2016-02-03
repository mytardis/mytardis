from abc import ABCMeta, abstractmethod

from compare import expect

from django.contrib.sites.models import RequestSite
from django.test import TestCase

import oaipmh.error
import oaipmh.interfaces

import pytz

from tardis.tardis_portal.models import Experiment, License, User, UserProfile
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
    exp_ids = [exp.id for exp in Experiment.objects]
    return 'experiment/%d' % min(exp_ids)
    

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
        self._experiment, self._experiment2, self._user = _create_test_data()

    def testIdentify(self):
        '''
        There can be only one provider that responds. This one does not.
        '''
        expect(lambda: self._getProvider().identify())\
            .to_raise(NotImplementedError)

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
            expect(header.identifier()).to_contain(str(e.id))
            expect(header.datestamp().replace(tzinfo=pytz.utc)) \
                .to_equal(get_local_time(e.update_time))
        # Remove public flag on first experiment
        self._experiment.public_access = Experiment.PUBLIC_ACCESS_NONE
        self._experiment.save()
        headers = self._getProvider() \
            .listIdentifiers(self._getProviderMetadataPrefix())
        # First is not public, so should not appear
        expect(len(headers)).to_equal(1)

    def testListIdentifiersDoesNotHandleSets(self):
        def call_with_set():
            self._getProvider() \
                .listIdentifiers(self._getProviderMetadataPrefix(),
                                 set='foo')
        expect(call_with_set).to_raise(oaipmh.error.NoSetHierarchyError)

    def testListMetadataFormats(self):
        expect(map(lambda t: t[0], self._getProvider().listMetadataFormats())) \
            .to_equal([self._getProviderMetadataPrefix()])

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
        expect(header.identifier()).to_contain(str(self._experiment.id))
        expect(header.datestamp().replace(tzinfo=pytz.utc))\
            .to_equal(get_local_time(self._experiment.update_time))
        expect(metadata.getField('title'))\
            .to_equal([str(self._experiment.title)])
        expect(metadata.getField('description'))\
            .to_equal([str(self._experiment.description)])
        expect(about).to_equal(None)

    def testListRecords(self):
        results = self._getProvider().listRecords('oai_dc')
        # Iterate through headers
        for header, metadata, _ in results:
            e = self._experiment if header.identifier() == _get_first_exp_id() \
                else self._experiment2
            expect(header.identifier()).to_contain(str(e.id))
            expect(header.datestamp().replace(tzinfo=pytz.utc))\
                .to_equal(get_local_time(e.update_time))
            expect(metadata.getField('title'))\
                .to_equal([str(e.title)])
            expect(metadata.getField('description'))\
                .to_equal([str(e.description)])
        # There should have been two
        expect(len(results)).to_equal(2)
        # Remove public flag on first one
        self._experiment.public_access = Experiment.PUBLIC_ACCESS_NONE
        self._experiment.save()
        headers = self._getProvider().listRecords('oai_dc')
        # First one not public, so should not appear
        expect(len(headers)).to_equal(1)


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
        expect(header.identifier()).to_contain(str(self._experiment.id))
        expect(header.datestamp().replace(tzinfo=pytz.utc))\
            .to_equal(get_local_time(self._experiment.update_time))
        expect(metadata.getField('id')).to_equal(self._experiment.id)
        expect(metadata.getField('title'))\
            .to_equal(str(self._experiment.title))
        expect(metadata.getField('description'))\
            .to_equal(str(self._experiment.description))
        expect(metadata.getField('licence_uri'))\
            .to_equal(License.get_none_option_license().url)
        expect(metadata.getField('licence_name'))\
            .to_equal(License.get_none_option_license().name)
        expect(metadata.getField('related_info'))\
            .to_equal([{'notes': 'This is a note.', \
                        'identifier': 'https://www.example.com/', \
                        'type': 'website', \
                        'id': 1, \
                        'title': 'Google'}])
        expect(len(metadata.getField('collectors')))\
            .to_equal(2)
        expect(about).to_equal(None)

    def testListRecords(self):
        results = self._getProvider().listRecords('rif')
        # Iterate through headers
        for header, metadata, _ in results:
            if header.identifier().startswith('experiment'):
                e = self._experiment if header.identifier() == _get_first_exp_id() \
                    else self._experiment2
                expect(header.identifier()).to_contain(str(e.id))
                expect(header.datestamp().replace(tzinfo=pytz.utc))\
                    .to_equal(get_local_time(e.update_time))
                expect(metadata.getField('title'))\
                    .to_equal(str(e.title))
                expect(metadata.getField('description'))\
                    .to_equal(str(e.description))
                expect(metadata.getField('licence_uri'))\
                    .to_equal(License.get_none_option_license().url)
                expect(metadata.getField('licence_name'))\
                    .to_equal(License.get_none_option_license().name)
                if e == self._experiment:
                    expect(metadata.getField('related_info'))\
                        .to_equal([{'notes': 'This is a note.', \
                                        'identifier': 'https://www.example.com/', \
                                        'type': 'website', \
                                        'id': 1, \
                                        'title': 'Google'}])
                else:
                    expect(metadata.getField('related_info')).to_equal([{}])
            else:
                expect(header.identifier()).to_contain(str(self._user.id))
                expect(header.datestamp().replace(tzinfo=pytz.utc))\
                    .to_equal(get_local_time(self._user.last_login))
                expect(metadata.getField('id')).to_equal(self._user.id)
                expect(metadata.getField('email'))\
                    .to_equal(str(self._user.email))
                expect(metadata.getField('given_name'))\
                    .to_equal(str(self._user.first_name))
                expect(metadata.getField('family_name'))\
                    .to_equal(str(self._user.last_name))
        # There should have been two
        expect(len(results)).to_equal(2)
        # Remove public flag on first experiment
        self._experiment.public_access = Experiment.PUBLIC_ACCESS_NONE
        self._experiment.save()
        headers = self._getProvider().listRecords('rif')
        # Should now be one
        expect(len(headers)).to_equal(1)

    def tearDown(self):
        pass
