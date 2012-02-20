from django.test import TestCase
from django.test.client import Client

from lxml import etree

from ..server import ServerImpl

class EndpointTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def testEndpointCanIdentify(self):
        response = self.client.get('/apps/oaipmh/?verb=Identify')
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        namespaces = {'oai': 'http://www.openarchives.org/OAI/2.0/'}
        assert xml.xpath('/oai:OAI-PMH', namespaces=namespaces)
        assert not xml.xpath('oai:error', namespaces=namespaces)
        assert xml.xpath('oai:Identify', namespaces=namespaces)

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
        except NotImplementedError:
            self.fail("Should be implemented.")

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
