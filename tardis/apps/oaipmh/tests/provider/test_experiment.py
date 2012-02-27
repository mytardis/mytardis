from abc import ABCMeta, abstractmethod

from compare import expect

from django.contrib.auth.models import User
from django.contrib.sites.models import RequestSite
from django.test import TestCase

import oaipmh.error
import oaipmh.interfaces

import pytz

from tardis.tardis_portal.creativecommonshandler import CreativeCommonsHandler
from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.util import get_local_time

from ...provider.experiment import AbstractExperimentProvider, \
    DcExperimentProvider, RifCsExperimentProvider

def _create_test_data():
    user = User(username='testuser')
    user.save()
    experiment = Experiment(title='Norwegian Blue',
                            description='Parrot + 40kV',
                            created_by=user)
    experiment.public = True
    experiment.save()
    cc_uri = 'http://creativecommons.org/licenses/by-nd/2.5/au/'
    cc_name = 'Creative Commons Attribution-NoDerivs 2.5 Australia'
    cch = CreativeCommonsHandler(experiment_id=experiment.id)
    psm = cch.get_or_create_cc_parameterset()
    psm.set_param("license_name", cc_name, "License Name")
    psm.set_param("license_uri", cc_uri, "License URI")
    return experiment

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
        self._experiment = _create_test_data()

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
        headers = self._getProvider().listIdentifiers(self._getProviderMetadataPrefix())
        # Iterate through headers
        for header in headers:
            expect(header.identifier()).to_contain(str(self._experiment.id))
            expect(header.datestamp().replace(tzinfo=pytz.utc))\
                .to_equal(get_local_time(self._experiment.update_time))
        # There should only have been one
        expect(len(headers)).to_equal(1)
        # Remove public flag
        self._experiment.public = False
        self._experiment.save()
        headers = self._getProvider() \
            .listIdentifiers(self._getProviderMetadataPrefix())
        # Not public, so should not appear
        expect(len(headers)).to_equal(0)

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
                                                                'experiment/1')
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
            expect(header.identifier()).to_contain(str(self._experiment.id))
            expect(header.datestamp().replace(tzinfo=pytz.utc))\
                .to_equal(get_local_time(self._experiment.update_time))
            expect(metadata.getField('title'))\
                .to_equal([str(self._experiment.title)])
            expect(metadata.getField('description'))\
                .to_equal([str(self._experiment.description)])
        # There should only have been one
        expect(len(results)).to_equal(1)
        # Remove public flag
        self._experiment.public = False
        self._experiment.save()
        headers = self._getProvider().listRecords('oai_dc')
        # Not public, so should not appear
        expect(len(headers)).to_equal(0)


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
                                                                'experiment/1')
        expect(header.identifier()).to_contain(str(self._experiment.id))
        expect(header.datestamp().replace(tzinfo=pytz.utc))\
            .to_equal(get_local_time(self._experiment.update_time))
        expect(metadata.getField('id')).to_equal(self._experiment.id)
        expect(metadata.getField('title'))\
            .to_equal(str(self._experiment.title))
        expect(metadata.getField('description'))\
            .to_equal(str(self._experiment.description))
        expect(metadata.getField('licence_uri'))\
            .to_equal('http://creativecommons.org/licenses/by-nd/2.5/au/')
        expect(metadata.getField('licence_name'))\
            .to_equal('Creative Commons Attribution-NoDerivs 2.5 Australia')
        expect(about).to_equal(None)

    def testListRecords(self):
        results = self._getProvider().listRecords('rif')
        # Iterate through headers
        for header, metadata, _ in results:
            expect(header.identifier()).to_contain(str(self._experiment.id))
            expect(header.datestamp().replace(tzinfo=pytz.utc))\
                .to_equal(get_local_time(self._experiment.update_time))
            expect(metadata.getField('title'))\
                .to_equal(str(self._experiment.title))
            expect(metadata.getField('description'))\
                .to_equal(str(self._experiment.description))
            expect(metadata.getField('licence_uri'))\
                .to_equal('http://creativecommons.org/licenses/by-nd/2.5/au/')
            expect(metadata.getField('licence_name'))\
                .to_equal('Creative Commons Attribution-NoDerivs 2.5 Australia')
        # There should only have been one
        expect(len(results)).to_equal(1)
        # Remove public flag
        self._experiment.public = False
        self._experiment.save()
        headers = self._getProvider().listRecords('rif')
        # Not public, so should not appear
        expect(len(headers)).to_equal(0)

    def tearDown(self):
        pass
