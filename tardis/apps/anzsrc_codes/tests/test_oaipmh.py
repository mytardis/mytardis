import json
import re

from bs4 import BeautifulSoup
from compare import expect, ensure, matcher

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from lxml import etree

from tardis.tardis_portal.models import \
    Experiment, License, ObjectACL, User, UserProfile
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager


def _create_user_and_login(username='testuser', password='testpass'):
    user = User.objects.create_user(username, '', password)
    user.save()
    UserProfile(user=user).save()

    client = Client()
    client.login(username=username, password=password)
    return (user, client)

class RifCSTestCase(TestCase):

    def setUp(self):
        self.ns = {'r': 'http://ands.org.au/standards/rif-cs/registryObjects',
                   'o': 'http://www.openarchives.org/OAI/2.0/'}
        user, client = _create_user_and_login()

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
        acl = ObjectACL(content_object=experiment,
                        pluginId='django_user',
                        entityId=str(user.id),
                        isOwner=False,
                        canRead=True,
                        canWrite=True,
                        canDelete=False,
                        aclOwnershipType=ObjectACL.OWNER_OWNED)
        acl.save()

        params = {'code': '010107',
                  'name': 'Mathematical Logic, Set Theory, Lattices and Universal Algebra',
                  'uri': 'http://purl.org/asc/1297.0/2008/for/010107'}
        response = client.post(\
                    reverse('tardis.apps.anzsrc_codes.views.'\
                            +'list_or_create_for_code',
                            args=[experiment.id]),
                    data=json.dumps(params),
                    content_type='application/json')
        # Check related info was created
        expect(response.status_code).to_equal(201)

        self.acl = acl
        self.client = client
        self.experiment = experiment
        self.params = params

    def testExistsInOaipmh(self):
        ns = self.ns
        args = {
            'verb': 'GetRecord',
            'metadataPrefix': 'rif',
            'identifier': 'experiment/%d' % self.experiment.id
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
        registryObject = metadata.xpath('r:registryObjects/r:registryObject',
                                           namespaces=ns)[0]
        # <collection type="dataset">
        expect(registryObject.xpath('r:collection/@type',
                                    namespaces=ns)[0]).to_equal('dataset')
        collection = registryObject.xpath('r:collection', namespaces=ns)[0]
        expect(collection.xpath('r:subject/@type', namespaces=ns)) \
            .to_equal(['anzsrc-for'])
        expect(collection.xpath('r:subject/text()', namespaces=ns)) \
            .to_equal([self.params['code']])
