import json

from django.test import TransactionTestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from lxml import etree

from tardis.tardis_portal.models import Experiment, License, ObjectACL, User


def _create_user_and_login(username='testuser', password='testpass'):
    user = User.objects.create_user(username, '', password)
    user.save()

    client = Client()
    client.login(username=username, password=password)
    return user, client


class RifCSTestCase(TransactionTestCase):

    def setUp(self):
        self.ns = {'r': 'http://ands.org.au/standards/rif-cs/registryObjects',
                   'o': 'http://www.openarchives.org/OAI/2.0/'}
        user, client = _create_user_and_login()

        license_ = License(name='Creative Commons Attribution-NoDerivs '
                                '2.5 Australia',
                           url='http://creativecommons.org/licenses/by-nd/'
                               '2.5/au/',
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

        params = {'type': 'website',
                  'identifier': 'https://www.google.com/',
                  'title': 'Google',
                  'notes': 'This is a note.'}
        response = client.post(\
                    reverse('tardis.apps.related_info.views.' +
                            'list_or_create_related_info',
                            args=[experiment.id]),
                    data=json.dumps(params),
                    content_type='application/json')
        # Check related info was created
        self.assertEqual(response.status_code, 201)

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
                                   '&'.join(['%s=%s' % (k, v)
                                             for k, v in args.items()]))
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        xml = etree.fromstring(response.content)
        print response.content
        assert xml.xpath('/o:OAI-PMH', namespaces=ns)
        assert not xml.xpath('o:error', namespaces=ns)
        assert xml.xpath('/o:OAI-PMH/o:GetRecord/o:record', namespaces=ns)
        header, metadata = xml.xpath('/o:OAI-PMH/o:GetRecord/o:record/o:*',
                                     namespaces=ns)[0:2]
        exp_id = Experiment.objects.first().id
        self.assertEqual(
            header.xpath('o:identifier/text()',namespaces=ns)[0],
            'experiment/%d' % exp_id)
        # <registryObject group="MyTARDIS Default Group">
        registryObject = metadata.xpath('r:registryObjects/r:registryObject',
                                        namespaces=ns)[0]
        # <collection type="dataset">
        self.assertEqual(registryObject.xpath('r:collection/@type',
                                    namespaces=ns)[0], 'dataset')
        collection = registryObject.xpath('r:collection', namespaces=ns)[0]
        self.assertEqual(
            collection.xpath('r:relatedInfo/@type', namespaces=ns),
            [self.params['type']])
        relatedInfo = collection.xpath('r:relatedInfo', namespaces=ns)[0]
        for k, v in self.params.items():
            if k == 'type':
                continue
            self.assertEqual(
                relatedInfo.xpath('r:'+k+'/text()', namespaces=ns), [v])
        self.assertEqual(
            relatedInfo.xpath('r:identifier/@type', namespaces=ns), ['uri'])
