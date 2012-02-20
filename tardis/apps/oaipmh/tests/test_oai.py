from django.test import TestCase
from django.test.client import Client

from ..server import ServerImpl

class EndpointTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def testEndpointExists(self):
        try:
            response = self.client.get('/apps/oaipmh/?verb=Identify')
            self.assertEqual(response.status_code, 200)
        except NotImplementedError:
            # This is OK for the moment
            pass

    def tearDown(self):
        pass

class ServerImplTestCase(TestCase):

    def setUp(self):
        self.server = ServerImpl()

    def testGetRecord(self):
        try:
            self.server.getRecord('oai_dc', 'MyTardis-1')
            self.fail("Not implemented yet.")
        except NotImplementedError:
            pass

    def testIdentify(self):
        try:
            self.server.identify()
            self.fail("Not implemented yet.")
        except NotImplementedError:
            pass

    def testListIdentifiers(self):
        try:
            self.server.listIdentifiers('oai_dc')
            self.fail("Not implemented yet.")
        except NotImplementedError:
            pass

    def testListMetadataFormats(self):
        try:
            self.server.listMetadataFormats()
            self.fail("Not implemented yet.")
        except NotImplementedError:
            pass

    def testListRecords(self):
        try:
            self.server.listRecords('oai_dc')
            self.fail("Not implemented yet.")
        except NotImplementedError:
            pass

    def testListSets(self):
        try:
            self.server.listSets()
            self.fail("Not implemented yet.")
        except NotImplementedError:
            pass

    def tearDown(self):
        pass
