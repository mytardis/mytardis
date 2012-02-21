from compare import expect

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from lxml import etree

import oaipmh.error
import pytz

from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.util import get_local_time

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
        user = User(username='testuser')
        user.save()
        experiment = Experiment(title='Norwegian Blue',
                                description='Parrot + 40kV',
                                created_by=user)
        experiment.public = True
        experiment.save()
        self._experiment = experiment


    def testGetRecord(self):
        header, metadata, about = self.server.getRecord('oai_dc',
                                                        'experiment/1')
        expect(header.identifier()).to_contain(str(self._experiment.id))
        expect(header.datestamp().replace(tzinfo=pytz.utc))\
            .to_equal(get_local_time(self._experiment.update_time))
        expect(metadata.getField('title'))\
            .to_equal([str(self._experiment.title)])
        expect(metadata.getField('description'))\
            .to_equal([str(self._experiment.description)])
        expect(about).to_equal(None)

    def testGetRecordHandlesInvalidIdentifiers(self):
        for id_ in ['experiment-1', 'MyTardis/1']:
            try:
                self.server.getRecord('oai_dc', id_)
                self.fail("Should raise exception.")
            except oaipmh.error.IdDoesNotExistError:
                pass

    def testIdentify(self):
        identify = self.server.identify()
        expect(identify.protocolVersion()).to_equal('2.0')

    def testListIdentifiers(self):
        headers = self.server.listIdentifiers('oai_dc')
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
        headers = self.server.listIdentifiers('oai_dc')
        # Not public, so should not appear
        expect(len(headers)).to_equal(0)

    def testListIdentifiersDoesNotHandleSets(self):
        try:
            self.server.listIdentifiers('oai_dc', set='foo')
            self.fail("Should have raised an error.")
        except oaipmh.error.NoSetHierarchyError:
            pass
        except NotImplementedError:
            self.fail("Should be implemented.")

    def testListMetadataFormats(self):
        formats = self.server.listMetadataFormats()
        expect(map(lambda t: t[0], formats)).to_equal(['oai_dc'])

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
