from django.contrib.sites.requests import RequestSite
from django.test import TestCase

import oaipmh.error
import oaipmh.interfaces

from ...provider.base import BaseProvider


class BaseProviderTestCase(TestCase):
    def setUp(self):
        class FakeRequest:
            def get_host(self):
                return "example.test"

        self.provider = BaseProvider(RequestSite(FakeRequest()))

    def testGetRecord(self):
        """
        Default behaviour should be to not handle the identifier.
        """
        with self.assertRaises(oaipmh.error.IdDoesNotExistError):
            self.provider.getRecord("rif", "experiment/1")()

    def testIdentify(self):
        """
        There can be only one provider that responds. By default, don't.
        """
        with self.assertRaises(NotImplementedError):
            self.provider.identify()

    def testListIdentifiers(self):
        """
        By default a provider cannot handle the given metadata prefix.
        """
        with self.assertRaises(oaipmh.error.CannotDisseminateFormatError):
            self.provider.listIdentifiers("oai_dc")()

    def testListMetadataFormats(self):
        """
        By default a provider handles no metadata formats.
        """
        self.assertEqual(self.provider.listMetadataFormats(), [])

    def testListRecords(self):
        """
        By default a provider cannot handle the given metadata prefix.
        """
        with self.assertRaises(oaipmh.error.CannotDisseminateFormatError):
            self.provider.listRecords("oai_dc")()

    def testListSets(self):
        """
        By default a provider does not implement sets.
        """
        with self.assertRaises(oaipmh.error.NoSetHierarchyError):
            self.provider.listSets()

    def tearDown(self):
        self.provider = None
