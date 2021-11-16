from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from lxml import etree

from tardis.tardis_portal.models import Experiment, License, ExperimentACL


def _create_test_data():
    user = User(username='tom',
                first_name='Thomas',
                last_name='Atkins',
                email='tommy@atkins.net')
    user.save()
    license_ = License(name='Creative Commons Attribution-NoDerivs 2.5 Australia',
                       url='http://creativecommons.org/licenses/by-nd/2.5/au/',
                       internal_description='CC BY 2.5 AU',
                       allows_distribution=True)
    license_.save()
    experiment = Experiment(title='Norwegian Blue',
                            description='Parrot + 40kV',
                            created_by=user)
    experiment.public_access = Experiment.PUBLIC_ACCESS_FULL
    experiment.license = license_
    experiment.save()
    experiment.experimentauthor_set.create(order=0,
                                           author="John Cleese",
                                           url="http://nla.gov.au/nla.party-1")
    experiment.experimentauthor_set.create(order=1,
                                           author="Michael Palin",
                                           url="http://nla.gov.au/nla.party-2")
    acl = ExperimentACL(experiment=experiment,
                    user=user,
                    isOwner=True,
                    canRead=True,
                    canDownload=True,
                    canWrite=True,
                    canSensitive=True,
                    canDelete=True,
                    aclOwnershipType=ExperimentACL.OWNER_OWNED)
    acl.save()
    return user, experiment


class EndpointTestCase(TestCase):

    def setUp(self):
        self._client = Client()
        self.ns = {'r': 'http://ands.org.au/standards/rif-cs/registryObjects',
                   'o': 'http://www.openarchives.org/OAI/2.0/'}

    def testIdentify(self):
        response = self._client_get('/apps/oaipmh/?verb=Identify')
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        ns = {'oai': 'http://www.openarchives.org/OAI/2.0/'}
        assert xml.xpath('/oai:OAI-PMH', namespaces=ns)
        assert not xml.xpath('oai:error', namespaces=ns)
        assert xml.xpath('oai:Identify', namespaces=ns)

    def testGetRecord(self):
        ns = self.ns
        _, experiment = _create_test_data()
        args = {
            'verb': 'GetRecord',
            'metadataPrefix': 'rif',
            'identifier': 'experiment/%d' % experiment.id
        }
        response = self._client_get('/apps/oaipmh/?%s' %
                                        '&'.join(['%s=%s' % (k,v)
                                                  for k,v in args.items()]))
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        assert xml.xpath('/o:OAI-PMH', namespaces=ns)
        assert not xml.xpath('o:error', namespaces=ns)
        assert xml.xpath('/o:OAI-PMH/o:GetRecord/o:record', namespaces=ns)
        header, metadata = xml.xpath('/o:OAI-PMH/o:GetRecord/o:record/o:*',
                                     namespaces=ns)[0:2]
        self.assertEqual(
            header.xpath('o:identifier/text()',namespaces=ns)[0],
            'experiment/%d' % Experiment.objects.first().id)
        # <registryObject group="MyTARDIS Default Group">
        self.assertEqual(metadata.xpath('r:registryObjects/r:registryObject/@group',
                              namespaces=ns)[0], 'MyTardis Test Group')
        self._check_experiment_regobj(experiment,
                            metadata.xpath('r:registryObjects/r:registryObject',
                                           namespaces=ns)[0])

    def _check_experiment_regobj(self, experiment, registryObject):
        ns = self.ns
        # <key>keydomain.test.example/experiment/1</key>
        self.assertEqual(
            registryObject.xpath('r:key/text()', namespaces=ns)[0],
            'keydomain.test.example/experiment/%d' % experiment.id)
        # <originatingSource>http://keydomain.test.example/</originatingSource>
        self.assertEqual(
            registryObject.xpath('r:originatingSource/text()',
                                 namespaces=ns)[0],
            'http://example.com/')
        # <collection type="dataset">
        self.assertEqual(registryObject.xpath('r:collection/@type',
                                    namespaces=ns)[0], 'dataset')
        collection = registryObject.xpath('r:collection', namespaces=ns)[0]
        # <name type="primary">
        #     <namePart>Test</namePart>
        # </name>
        self.assertEqual(collection.xpath('r:name[@type="primary"]/r:namePart/text()',
                                namespaces=ns)[0], experiment.title)
        # <description type="brief">Test experiment description.</description>
        self.assertEqual(
            collection.xpath('r:description[@type="brief"]/text()',
                             namespaces=ns)[0],
            experiment.description)
        # <location>
        #   <address>
        #     <electronic type="url">
        #       <value>http://keydomain.test.example/experiment/view/1/</value>
        #     </electronic>
        #   </address>
        # </location>
        loc_xpath = 'r:location/r:address/r:electronic[@type="url"]'\
                    +'/r:value/text()'
        self.assertEqual(
            collection.xpath(loc_xpath, namespaces=ns)[0],
            'http://example.com/experiment/view/%d/' % experiment.id)
        # <rights>
        #     <accessRights>
        #         All data is publicly available online.
        #     </accessRights>
        #     <licence rightsUri="http://creativecommons.org/licenses/by-nd/2.5/au/">
        #         Creative Commons Attribution-NoDerivs 2.5 Australia
        #     </licence>
        # </location>
        self.assertEqual(
            collection.xpath('r:rights/r:accessRights/text()', namespaces=ns),
            ['All data is publicly available online.'])
        self.assertEqual(
            collection.xpath('r:rights/r:licence/@rightsUri', namespaces=ns),
            ['http://creativecommons.org/licenses/by-nd/2.5/au/'])
        self.assertEqual(
            collection.xpath('r:rights/r:licence/text()', namespaces=ns),
            ['Creative Commons Attribution-NoDerivs 2.5 Australia'])
        # <relatedObject>
        #     <key>user/1</key>
        #     <relation type="isManagedBy"/>
        # </relatedObjexperimentect>
        self.assertEqual(
            collection.xpath(
                'r:relatedObject[r:relation/@type="isManagedBy"]/r:key/text()',
                namespaces=ns),
            ['keydomain.test.example/user/%d' % User.objects.all().exclude(id = settings.PUBLIC_USER_ID).first().id])
        self.assertEqual(
            collection.xpath(
                'r:relatedObject[r:relation/@type="hasCollector"]/r:key/text()',
                namespaces=ns),
                ["http://nla.gov.au/nla.party-%d" % i for i in (1, 2)])

    def _check_user_regobj(self, user, registryObject):
        ns = self.ns
        # <key>keydomain.test.example/experiment/1</key>
        self.assertEqual(
            registryObject.xpath('r:key/text()', namespaces=ns)[0],
            'keydomain.test.example/user/%d' % user.id)
        # <originatingSource>http://keydomain.test.example/</originatingSource>
        self.assertEqual(
            registryObject.xpath(
                'r:originatingSource/text()', namespaces=ns)[0],
                'http://example.com/')
        # <collection type="dataset">
        self.assertEqual(
            registryObject.xpath('r:party/@type', namespaces=ns)[0], 'person')
        collection = registryObject.xpath('r:party', namespaces=ns)[0]
        # <name type="primary">
        #     <namePart type="given">Thomas</namePart>
        #     <namePart type="family">Atkins</namePart>
        # </name>
        self.assertEqual(collection.xpath('r:name[@type="primary"]/'+
                                'r:namePart[@type="given"]/text()',
                                namespaces=ns)[0], user.first_name)
        self.assertEqual(collection.xpath('r:name[@type="primary"]/'+
                                'r:namePart[@type="family"]/text()',
                                namespaces=ns)[0], user.last_name)
        # <location>
        #     <address>
        #         <electronic type="email">tommy@atkins.net</electronic>
        #     </address>
        # </location>
        loc_xpath = 'r:location/r:address/r:electronic[@type="email"]'\
                    +'/r:value/text()'
        self.assertEqual(
            collection.xpath(loc_xpath, namespaces=ns)[0],
            user.email)
        # <relatedObject>
        #     <key>user/1</key>
        #     <relation type="isManagerOf"/>
        # </relatedObjexperimentect>
        self.assertEqual(
            collection.xpath(
                'r:relatedObject[r:relation/@type="isManagerOf"]/r:key/text()',
                namespaces=ns),
                ['keydomain.test.example/experiment/%d' %
                 Experiment.objects.first().id])

    def testListIdentifiers(self):
        user, experiment = _create_test_data()
        args = {
            'verb': 'ListIdentifiers',
            'metadataPrefix': 'rif'
        }
        response = self._client_get('/apps/oaipmh/?%s' %
                                        '&'.join('%s=%s' % (k,v)
                                                 for k,v in args.items()))
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        ns = {'r': 'http://ands.org.au/standards/rif-cs/registryObjects',
              'o': 'http://www.openarchives.org/OAI/2.0/'}
        assert xml.xpath('/o:OAI-PMH', namespaces=ns)
        assert not xml.xpath('o:error', namespaces=ns)
        idents = xml.xpath('/o:OAI-PMH/o:ListIdentifiers/o:header/o:identifier',
                           namespaces=ns)
        assert len(idents) == 2
        assert 'experiment/%d' % experiment.id in [i.text for i in idents]
        assert 'user/%d' % user.id in [i.text for i in idents]

    def testListMetadataFormats(self):
        ns = self.ns
        # Without Identifier
        _, experiment = _create_test_data()
        args = {
            'verb': 'ListMetadataFormats'
        }
        response = self._client_get('/apps/oaipmh/?%s' %
                                        '&'.join('%s=%s' % (k,v)
                                                 for k,v in args.items()))
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        assert xml.xpath('/o:OAI-PMH', namespaces=ns)
        assert not xml.xpath('o:error', namespaces=ns)
        formats = xml.xpath('/o:OAI-PMH/o:ListMetadataFormats' +
                            '/o:metadataFormat/o:metadataPrefix',
                            namespaces=ns)
        self.assertEqual(
            sorted([fmt.text for fmt in formats]),
            ['oai_dc', 'rif'])
        # With Identifier
        args = {
            'verb': 'ListMetadataFormats',
            'identifier': 'experiment/%d' % experiment.id
        }
        response = self._client_get('/apps/oaipmh/?%s' %
                                        '&'.join('%s=%s' % (k,v)
                                                 for k,v in args.items()))
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        assert xml.xpath('/o:OAI-PMH', namespaces=ns)
        assert not xml.xpath('o:error', namespaces=ns)
        formats = xml.xpath('/o:OAI-PMH/o:ListMetadataFormats' +
                            '/o:metadataFormat/o:metadataPrefix',
                            namespaces=ns)
        self.assertEqual(
            sorted([fmt.text for fmt in formats]),
            ['oai_dc', 'rif'])


    def testListRecords(self):
        ns = self.ns
        user, experiment = _create_test_data()
        args = {
            'verb': 'ListRecords',
            'metadataPrefix': 'rif'
        }
        response = self._client_get('/apps/oaipmh/?%s' %
                                        '&'.join('%s=%s' % (k,v)
                                                 for k,v in args.items()))
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        assert xml.xpath('/o:OAI-PMH', namespaces=ns)
        assert not xml.xpath('o:error', namespaces=ns)
        idents = xml.xpath('/o:OAI-PMH/o:ListRecords'+
                           '/o:record/o:header/o:identifier',
                           namespaces=ns)
        assert len(idents) == 2
        assert 'experiment/%d' % experiment.id in [i.text for i in idents]
        assert 'user/%d' % user.id in [i.text for i in idents]
        metadata_xpath = '/o:OAI-PMH/o:ListRecords/o:record/o:metadata'
        metadata = xml.xpath(metadata_xpath, namespaces=ns)
        assert len(metadata) == 2
        collectionObject = xml.xpath(metadata_xpath +
                                     '/r:registryObjects/r:registryObject' +
                                     '[r:collection]',
                                     namespaces=ns)
        assert len(collectionObject) == 1
        self._check_experiment_regobj(experiment, collectionObject[0])
        partyObject = xml.xpath(metadata_xpath +
                                '/r:registryObjects/r:registryObject' +
                                '[r:party]',
                                namespaces=ns)
        assert len(partyObject) == 1
        self._check_user_regobj(user, partyObject[0])

    def _client_get(self, url):
        return self._client.get(url)

    def tearDown(self):
        pass
