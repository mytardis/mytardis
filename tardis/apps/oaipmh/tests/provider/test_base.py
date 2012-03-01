from compare import expect

from django.contrib.sites.models import RequestSite
from django.test import TestCase

import oaipmh.error
import oaipmh.interfaces

from ...provider.base import BaseProvider

class BaseProviderTestCase(TestCase):

    def setUp(self):
        class FakeRequest():
            def get_host(self):
                return 'example.test'
        self.provider = BaseProvider(RequestSite(FakeRequest()))

    def testGetRecord(self):
        '''
        Default behaviour should be to not handle the identifier.
        '''
        expect(lambda: self.provider.getRecord('rif', 'experiment/1'))\
            .to_raise(oaipmh.error.IdDoesNotExistError)

    def testIdentify(self):
        '''
        There can be only one provider that responds. By default, don't.
        '''
        expect(lambda: self.provider.identify())\
            .to_raise(NotImplementedError)

    def testListIdentifiers(self):
        '''
        By default a provider cannot handle the given metadata prefix.
        '''
        expect(lambda: self.provider.listIdentifiers('oai_dc'))\
            .to_raise(oaipmh.error.CannotDisseminateFormatError)

    def testListMetadataFormats(self):
        '''
        By default a provider handles no metadata formats.
        '''
        expect(lambda: self.provider.listMetadataFormats())\
            .to_return([])

    def testListRecords(self):
        '''
        By default a provider cannot handle the given metadata prefix.
        '''
        expect(lambda: self.provider.listRecords('oai_dc'))\
            .to_raise(oaipmh.error.CannotDisseminateFormatError)

    def testListSets(self):
        '''
        By default a provider does not implement sets.
        '''
        expect(lambda: self.provider.listSets())\
            .to_raise(oaipmh.error.NoSetHierarchyError)

    def tearDown(self):
        self.provider = None
