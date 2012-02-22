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

def _create_test_data():
    user = User(username='testuser')
    user.save()
    experiment = Experiment(title='Norwegian Blue',
                            description='Parrot + 40kV',
                            created_by=user)
    experiment.public = True
    experiment.save()
    return experiment

class EndpointTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def testIdentify(self):
        response = self.client.get('/apps/oaipmh/?verb=Identify')
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        ns = {'oai': 'http://www.openarchives.org/OAI/2.0/'}
        assert xml.xpath('/oai:OAI-PMH', namespaces=ns)
        assert not xml.xpath('oai:error', namespaces=ns)
        assert xml.xpath('oai:Identify', namespaces=ns)


    def testGetRecord(self):
        experiment = _create_test_data()
        args = {
            'verb': 'GetRecord',
            'metadataPrefix': 'rif',
            'identifier': 'experiment/1'
        }
        response = self.client.get('/apps/oaipmh/?%s' %
                                   '&'.join('%s=%s' % (k,v)
                                            for k,v in args.items()))
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        ns = {'r': 'http://ands.org.au/standards/rif-cs/registryObjects',
              'o': 'http://www.openarchives.org/OAI/2.0/'}
        assert xml.xpath('/o:OAI-PMH', namespaces=ns)
        assert not xml.xpath('o:error', namespaces=ns)
        assert xml.xpath('/o:OAI-PMH/o:GetRecord/o:record', namespaces=ns)
        header, metadata = xml.xpath('/o:OAI-PMH/o:GetRecord/o:record/o:*',
                                     namespaces=ns)[0:2]
        expect(header.xpath('o:identifier/text()',namespaces=ns)[0]) \
            .to_equal('experiment/1')
        # <registryObject group="MyTARDIS Default Group">
        expect(metadata.xpath('r:registryObjects/r:registryObject/@group',
                              namespaces=ns)[0]).to_equal('MyTardis Test Group')
        registryObject = metadata.xpath('r:registryObjects/r:registryObject',
                                        namespaces=ns)[0]
        # <key>example.com/experiment/1</key>
        expect(registryObject.xpath('r:key/text()', namespaces=ns)[0])\
            .to_equal('example.com/experiment/1')
        # <originatingSource>http://example.com/</originatingSource>
        expect(registryObject.xpath('r:originatingSource/text()',
                                    namespaces=ns)[0]) \
                                    .to_equal('http://example.com/')
        # <collection type="dataset">
        expect(registryObject.xpath('r:collection/@type',
                                    namespaces=ns)[0]).to_equal('dataset')
        collection = registryObject.xpath('r:collection', namespaces=ns)[0]
        # <name type="primary">
        #     <namePart>Test</namePart>
        # </name>
        expect(collection.xpath('r:name[@type="primary"]/r:namePart/text()',
                                namespaces=ns)[0]).to_equal('Norwegian Blue')
        # <description type="brief">Test experiment description.</description>
        expect(collection.xpath('r:description[@type="brief"]/text()',
                                namespaces=ns)[0]).to_equal('Parrot + 40kV')
        # <location>
        #     <address>
        #         <electronic type="url">http://example.com/experiment/view/1/</electronic>
        #     </address>
        # </location>
        loc_xpath = 'r:location/r:address/r:electronic[@type="url"]/text()'
        expect(collection.xpath(loc_xpath, namespaces=ns)[0]) \
                .to_equal('http://example.com/experiment/view/1/')





    def tearDown(self):
        pass


class ServerImplTestCase(TestCase):

    def setUp(self):
        self.server = ServerImpl()
        self._experiment = _create_test_data()

    def testGetRecord(self):
        header, metadata, about = self.server.getRecord('rif',
                                                        'experiment/1')
        expect(header.identifier()).to_contain(str(self._experiment.id))
        expect(header.datestamp().replace(tzinfo=pytz.utc))\
            .to_equal(get_local_time(self._experiment.update_time))
        expect(metadata.getField('id')).to_equal(self._experiment.id)
        expect(metadata.getField('title'))\
            .to_equal(str(self._experiment.title))
        expect(metadata.getField('description'))\
            .to_equal(str(self._experiment.description))
        expect(about).to_equal(None)

    def testGetRecordOaiDc(self):
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
