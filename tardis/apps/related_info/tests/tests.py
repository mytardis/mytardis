import json
import re

from bs4 import BeautifulSoup
from compare import expect, matcher

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from lxml import etree

from tardis.tardis_portal.models import \
    Experiment, ExperimentACL, User, UserProfile
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager


@matcher
def to_match(self, regex):
    assert re.search(regex, self.value)

def _create_user_and_login(username='testuser', password='testpass'):
    user = User.objects.create_user(username, '', password)
    user.save()
    UserProfile(user=user).save()

    client = Client()
    client.login(username=username, password=password)
    return (user, client)

class TabTestCase(TestCase):

    def setUp(self):
        user, client = _create_user_and_login()

        experiment = Experiment(title='Norwegian Blue',
                                description='Parrot + 40kV',
                                created_by=user)
        experiment.save()
        acl = ExperimentACL(experiment=experiment,
                            pluginId='django_user',
                            entityId=str(user.id),
                            isOwner=False,
                            canRead=True,
                            canWrite=False,
                            canDelete=False,
                            aclOwnershipType=ExperimentACL.OWNER_OWNED)
        acl.save()
        self.client = client
        self.experiment = experiment

    def testAccessWhenAnonymous(self):
        client = Client()
        response = client.get(\
                    reverse('tardis.apps.related_info.views.index',
                            args=[self.experiment.id]))
        expect(response.status_code).to_equal(403)

    def testAccessWhenLoggedIn(self):
        response = self.client.get(\
                    reverse('tardis.apps.related_info.views.index',
                            args=[self.experiment.id]))
        expect(response.status_code).to_equal(200)

class ListTestCase(TestCase):

    def setUp(self):
        user, client = _create_user_and_login()

        experiment = Experiment(title='Norwegian Blue',
                                description='Parrot + 40kV',
                                created_by=user)
        experiment.save()
        acl = ExperimentACL(experiment=experiment,
                            pluginId='django_user',
                            entityId=str(user.id),
                            isOwner=False,
                            canRead=True,
                            canWrite=False,
                            canDelete=False,
                            aclOwnershipType=ExperimentACL.OWNER_OWNED)
        acl.save()
        self.client = client
        self.experiment = experiment

    def testHandlesEmptySet(self):
        response = self.client.get(\
                    reverse('tardis.apps.related_info.views.list_related_info',
                            args=[self.experiment.id]))
        expect(response.status_code).to_equal(200)
        expect(response['Content-Type'])\
            .to_equal('application/json; charset=utf-8')
        expect(response.content).to_equal('[]')

    def testHandlesSingleEntry(self):
        from ..views import SCHEMA_URI
        psm = ParameterSetManager(parentObject=self.experiment,
                                  schema=SCHEMA_URI)
        params = {'type': 'website',
                  'identifier': 'https://www.google.com',
                  'title': 'Google',
                  'notes': 'This is a note.'}
        for k, v in params.items():
            psm.set_param(k, v)

        response = self.client.get(\
                    reverse('tardis.apps.related_info.views.list_related_info',
                            args=[self.experiment.id]))
        expect(response.status_code).to_equal(200)
        expect(response['Content-Type'])\
            .to_equal('application/json; charset=utf-8')

        objs = json.loads(response.content)
        expect(len(objs)).to_be(1)
        for k in params.keys():
            expect(objs[0][k]).to_equal(params[k])

    def testHandlesMultipleEntries(self):
        from ..views import SCHEMA_URI
        param_list = ({'type': 'website',
                       'identifier': 'https://www.example.test/%d' % i,
                       'title': 'Title #%d' % i,
                       'notes': 'This is note #%d.' % i} for i in range(10))
        for params in param_list:
            psm = ParameterSetManager(parentObject=self.experiment,
                                      schema=SCHEMA_URI)
            for k, v in params.items():
                psm.set_param(k, v)

        response = self.client.get(\
                    reverse('tardis.apps.related_info.views.list_related_info',
                            args=[self.experiment.id]))
        expect(response.status_code).to_equal(200)
        expect(response['Content-Type'])\
            .to_equal('application/json; charset=utf-8')

        objs = json.loads(response.content)
        expect(len(objs)).to_be(10)


        for obj in objs:
            expect(obj['type']).to_equal('website')
            expect(obj['identifier']).to_match(r'www.example.test/\d+$')
            expect(obj['title']).to_match(r'^Title #\d+$')
            expect(obj['notes']).to_match(r'note #\d+\.$')

class GetTestCase(TestCase):

    def setUp(self):
        user, client = _create_user_and_login()

        experiment = Experiment(title='Norwegian Blue',
                                description='Parrot + 40kV',
                                created_by=user)
        experiment.save()
        acl = ExperimentACL(experiment=experiment,
                            pluginId='django_user',
                            entityId=str(user.id),
                            isOwner=False,
                            canRead=True,
                            canWrite=False,
                            canDelete=False,
                            aclOwnershipType=ExperimentACL.OWNER_OWNED)
        acl.save()
        self.client = client
        self.experiment = experiment

    def testHandlesNotFound(self):
        response = self.client.get(\
                    reverse('tardis.apps.related_info.views.get_related_info',
                            args=[self.experiment.id, 0]))
        expect(response.status_code).to_equal(404)

    def testHandlesFound(self):
        from ..views import SCHEMA_URI
        psm = ParameterSetManager(parentObject=self.experiment,
                                  schema=SCHEMA_URI)
        params = {'type': 'website',
                  'identifier': 'https://www.google.com',
                  'title': 'Google',
                  'notes': 'This is a note.'}
        for k, v in params.items():
            psm.set_param(k, v)

        response = self.client.get(\
                    reverse('tardis.apps.related_info.views.get_related_info',
                            args=[self.experiment.id, psm.parameterset.id]))
        expect(response.status_code).to_equal(200)

        obj = json.loads(response.content)
        for k in params.keys():
            expect(obj[k]).to_equal(params[k])

