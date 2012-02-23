from compare import expect

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from lxml import etree

import oaipmh.error
import pytz

from tardis.tardis_portal.creativecommonshandler import CreativeCommonsHandler
from tardis.tardis_portal.models import Experiment

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

class EndpointTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.ns = {'r': 'http://ands.org.au/standards/rif-cs/registryObjects',
                   'o': 'http://www.openarchives.org/OAI/2.0/'}

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
        ns = self.ns
        experiment = _create_test_data()
        args = {
            'verb': 'GetRecord',
            'metadataPrefix': 'rif',
            'identifier': 'experiment/%d' % experiment.id
        }
        response = self.client.get('/apps/oaipmh/?%s' %
                                   '&'.join(['%s=%s' % (k,v)
                                            for k,v in args.items()]))
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        print response.content
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
        self._check_reg_obj(experiment,
                            metadata.xpath('r:registryObjects/r:registryObject',
                                           namespaces=ns)[0])

    def _check_reg_obj(self, experiment, registryObject):
        ns = self.ns
        # <key>example.com/experiment/1</key>
        expect(registryObject.xpath('r:key/text()', namespaces=ns)[0])\
            .to_equal('example.com/experiment/%d' % experiment.id)
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
                                namespaces=ns)[0]).to_equal(experiment.title)
        # <description type="brief">Test experiment description.</description>
        expect(collection.xpath('r:description[@type="brief"]/text()',
                                namespaces=ns)[0]) \
                                .to_equal(experiment.description)
        # <location>
        #     <address>
        #         <electronic type="url">
        #            http://example.com/experiment/view/1/
        #         </electronic>
        #     </address>
        # </location>
        loc_xpath = 'r:location/r:address/r:electronic[@type="url"]/text()'
        expect(collection.xpath(loc_xpath, namespaces=ns)[0]) \
                .to_equal('http://example.com/experiment/view/%d/' %
                          experiment.id)
        # <rights>
        #     <license rightsUri="http://creativecommons.org/licenses/by-nd/2.5/au/">
        #         Creative Commons Attribution-NoDerivs 2.5 Australia
        #     </license>
        # </location>
        expect(collection.xpath('r:rights/r:license/@rightsUri',
            namespaces=ns)) \
            .to_equal(['http://creativecommons.org/licenses/by-nd/2.5/au/'])
        expect(collection.xpath('r:rights/r:license/text()',
            namespaces=ns)) \
            .to_equal(['Creative Commons Attribution-NoDerivs 2.5 Australia'])

    def testListIdentifiers(self):
        experiment = _create_test_data()
        args = {
            'verb': 'ListIdentifiers',
            'metadataPrefix': 'rif'
        }
        response = self.client.get('/apps/oaipmh/?%s' %
                                   '&'.join('%s=%s' % (k,v)
                                            for k,v in args.items()))
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        ns = {'r': 'http://ands.org.au/standards/rif-cs/registryObjects',
              'o': 'http://www.openarchives.org/OAI/2.0/'}
        print response.content
        assert xml.xpath('/o:OAI-PMH', namespaces=ns)
        assert not xml.xpath('o:error', namespaces=ns)
        idents = xml.xpath('/o:OAI-PMH/o:ListIdentifiers/o:header/o:identifier',
                           namespaces=ns)
        assert len(idents) == 1
        assert idents[0].text == 'experiment/%d' % experiment.id

    def testListMetadataFormats(self):
        ns = self.ns
        # Without Identifier
        experiment = _create_test_data()
        args = {
            'verb': 'ListMetadataFormats'
        }
        response = self.client.get('/apps/oaipmh/?%s' %
                                   '&'.join('%s=%s' % (k,v)
                                            for k,v in args.items()))
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        print response.content
        assert xml.xpath('/o:OAI-PMH', namespaces=ns)
        assert not xml.xpath('o:error', namespaces=ns)
        formats = xml.xpath('/o:OAI-PMH/o:ListMetadataFormats/o:metadataFormat/o:metadataPrefix',
                            namespaces=ns)
        assert len(formats) == 2
        assert formats[0].text == 'oai_dc'
        assert formats[1].text == 'rif'
        # With Identifier
        args = {
            'verb': 'ListMetadataFormats',
            'identifier': 'experiment/%d' % experiment.id
        }
        response = self.client.get('/apps/oaipmh/?%s' %
                                   '&'.join('%s=%s' % (k,v)
                                            for k,v in args.items()))
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        print response.content
        assert xml.xpath('/o:OAI-PMH', namespaces=ns)
        assert not xml.xpath('o:error', namespaces=ns)
        formats = xml.xpath('/o:OAI-PMH/o:ListMetadataFormats/o:metadataFormat/o:metadataPrefix',
                            namespaces=ns)
        assert len(formats) == 2
        assert formats[0].text == 'oai_dc'
        assert formats[1].text == 'rif'


    def testListRecords(self):
        ns = self.ns
        experiment = _create_test_data()
        args = {
            'verb': 'ListRecords',
            'metadataPrefix': 'rif'
        }
        response = self.client.get('/apps/oaipmh/?%s' %
                                   '&'.join('%s=%s' % (k,v)
                                            for k,v in args.items()))
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        print response.content
        assert xml.xpath('/o:OAI-PMH', namespaces=ns)
        assert not xml.xpath('o:error', namespaces=ns)
        idents = xml.xpath('/o:OAI-PMH/o:ListRecords'+
                           '/o:record/o:header/o:identifier',
                           namespaces=ns)
        assert len(idents) == 1
        assert idents[0].text == 'experiment/%d' % experiment.id
        metadata = xml.xpath('/o:OAI-PMH/o:ListRecords/o:record/o:metadata',
                           namespaces=ns)
        assert len(metadata) == 1
        obj = metadata[0].getchildren()[0].getchildren()
        assert len(obj) == 1
        self._check_reg_obj(experiment, obj[0])



    def tearDown(self):
        pass

