import json
import re

from bs4 import BeautifulSoup
from compare import expect, ensure, matcher

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from lxml import etree

from tardis.tardis_portal.models import \
    Experiment, ObjectACL, User, UserProfile
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
        acl = ObjectACL(content_object=experiment,
                        pluginId='django_user',
                        entityId=str(user.id),
                        isOwner=False,
                        canRead=True,
                        canWrite=False,
                        canDelete=False,
                        aclOwnershipType=ObjectACL.OWNER_OWNED)
        acl.save()
        self.client = client
        self.experiment = experiment

    def testAccessWithoutReadPerms(self):
        client = Client()
        response = client.get(\
                    reverse('tardis.apps.related_info.views.index',
                            args=[self.experiment.id]))
        expect(response.status_code).to_equal(403)

    def testAccessWithReadPerms(self):
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
        acl = ObjectACL(content_object=experiment,
                        pluginId='django_user',
                        entityId=str(user.id),
                        isOwner=False,
                        canRead=True,
                        canWrite=False,
                        canDelete=False,
                        aclOwnershipType=ObjectACL.OWNER_OWNED)
        acl.save()
        self.client = client
        self.experiment = experiment

    def testHandlesEmptySet(self):
        response = self.client.get(\
                    reverse('tardis.apps.related_info.views.'\
                            +'list_or_create_related_info',
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
                  'identifier': 'https://www.google.com/',
                  'title': 'Google',
                  'notes': 'This is a note.'}
        for k, v in params.items():
            psm.set_param(k, v)

        response = self.client.get(\
                    reverse('tardis.apps.related_info.views.'\
                            +'list_or_create_related_info',
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
                    reverse('tardis.apps.related_info.views.'\
                            +'list_or_create_related_info',
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
        acl = ObjectACL(content_object=experiment,
                        pluginId='django_user',
                        entityId=str(user.id),
                        isOwner=False,
                        canRead=True,
                        canWrite=False,
                        canDelete=False,
                        aclOwnershipType=ObjectACL.OWNER_OWNED)
        acl.save()
        self.client = client
        self.experiment = experiment

    def testHandlesNotFound(self):
        response = self.client.get(\
                    reverse('tardis.apps.related_info.views.'\
                            +'get_or_update_or_delete_related_info',
                            args=[self.experiment.id, 0]))
        expect(response.status_code).to_equal(404)

    def testHandlesFound(self):
        from ..views import SCHEMA_URI
        psm = ParameterSetManager(parentObject=self.experiment,
                                  schema=SCHEMA_URI)
        params = {'type': 'website',
                  'identifier': 'https://www.google.com/',
                  'title': 'Google',
                  'notes': 'This is a note.'}
        for k, v in params.items():
            psm.set_param(k, v)

        response = self.client.get(\
                    reverse('tardis.apps.related_info.views.'\
                            +'get_or_update_or_delete_related_info',
                            args=[self.experiment.id, psm.parameterset.id]))
        expect(response.status_code).to_equal(200)

        obj = json.loads(response.content)
        for k in params.keys():
            expect(obj[k]).to_equal(params[k])


class CreateTestCase(TestCase):

    def setUp(self):
        user, client = _create_user_and_login()

        experiment = Experiment(title='Norwegian Blue',
                                description='Parrot + 40kV',
                                created_by=user)
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
        self.acl = acl
        self.client = client
        self.experiment = experiment

    def testMustHaveWrite(self):
        self.acl.canWrite = False
        self.acl.save()
        params = {'type': 'website',
                  'identifier': 'https://www.google.com/',
                  'title': 'Google',
                  'notes': 'This is a note.'}
        response = self.client.post(\
                    reverse('tardis.apps.related_info.views.'\
                            +'list_or_create_related_info',
                            args=[self.experiment.id]),
                    data=json.dumps(params),
                    content_type='application/json')
        expect(response.status_code).to_equal(403)

    def testCanCreate(self):
        params = {'type': 'website',
                  'identifier': 'https://www.google.com/',
                  'title': 'Google',
                  'notes': 'This is a note.'}
        response = self.client.post(\
                    reverse('tardis.apps.related_info.views.'\
                            +'list_or_create_related_info',
                            args=[self.experiment.id]),
                    data=json.dumps(params),
                    content_type='application/json')
        # Check that content reports as created, returns the created object
        expect(response.status_code).to_equal(201)
        obj = json.loads(response.content)
        ensure(type(obj['id']) == int, True,
               message='Created object should have an ID.')
        for k in params.keys():
            expect(obj[k]).to_equal(params[k])
        # Check that creation really did persist
        response = self.client.get(\
                    reverse('tardis.apps.related_info.views.'\
                            +'get_or_update_or_delete_related_info',
                            args=[self.experiment.id, obj['id']]))
        expect(response.status_code).to_equal(200)

    def testDetectsBadInput(self):
        def do_post(params):
            return self.client.post(\
                    reverse('tardis.apps.related_info.views.'\
                            +'list_or_create_related_info',
                            args=[self.experiment.id]),
                    data=json.dumps(params),
                    content_type='application/json')
        # We need an identifier
        params = {'type': 'website'}
        response = do_post(params)
        expect(response.status_code).to_equal(400)
        # We need a type
        params = {'identifier': 'http://www.google.com/'}
        response = do_post(params)
        expect(response.status_code).to_equal(400)
        # We need an identifier and URL
        params = {'type': 'website', 'identifier': 'http://www.google.com/'}
        response = do_post(params)
        expect(response.status_code).to_equal(201)


class UpdateTestCase(TestCase):

    def setUp(self):
        user, client = _create_user_and_login()

        experiment = Experiment(title='Norwegian Blue',
                                description='Parrot + 40kV',
                                created_by=user)
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
        self.acl = acl
        self.client = client
        self.experiment = experiment

    def _create_initial_entry(self):
        params = {'type': 'website',
                  'identifier': 'https://www.google.com/',
                  'title': 'Google',
                  'notes': 'This is a note.'}
        response = self.client.post(reverse('tardis.apps.related_info.views.'\
                                           +'list_or_create_related_info',
                                           args=[self.experiment.id]),
                                    data=json.dumps(params),
                                    content_type='application/json')
        expect(response.status_code).to_equal(201)
        return json.loads(response.content)


    def testMustHaveWrite(self):
        related_info_id = self._create_initial_entry()['id']
        self.acl.canWrite = False
        self.acl.save()
        params = {'type': 'website',
                  'identifier': 'https://www.google.com/'}
        response = self.client.put(\
                    reverse('tardis.apps.related_info.views.'\
                            +'get_or_update_or_delete_related_info',
                            args=[self.experiment.id, related_info_id]),
                    data=json.dumps(params),
                    content_type='application/json')
        expect(response.status_code).to_equal(403)

    def testDetectsBadInput(self):
        def do_put(params):
            return self.client.put(\
                    reverse('tardis.apps.related_info.views.'\
                            +'get_or_update_or_delete_related_info',
                            args=[self.experiment.id,
                                  self._create_initial_entry()['id']]),
                    data=json.dumps(params),
                    content_type='application/json')
        # We need an identifier
        params = {'type': 'website'}
        response = do_put(params)
        expect(response.status_code).to_equal(400)
        # We need a type
        params = {'identifier': 'http://www.google.com/'}
        response = do_put(params)
        expect(response.status_code).to_equal(400)
        # We need an identifier and URL
        params = {'type': 'website',
                  'identifier': 'http://www.google.com/'}
        response = do_put(params)
        expect(response.status_code).to_equal(201)


class DeleteTestCase(TestCase):

    def setUp(self):
        user, client = _create_user_and_login()

        experiment = Experiment(title='Norwegian Blue',
                                description='Parrot + 40kV',
                                created_by=user)
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
        self.acl = acl
        self.client = client
        self.experiment = experiment

    def _create_initial_entry(self):
        params = {'type': 'website',
                  'identifier': 'https://www.google.com/',
                  'title': 'Google',
                  'notes': 'This is a note.'}
        response = self.client.post(reverse('tardis.apps.related_info.views.'\
                                           +'list_or_create_related_info',
                                           args=[self.experiment.id]),
                                    data=json.dumps(params),
                                    content_type='application/json')
        expect(response.status_code).to_equal(201)
        return json.loads(response.content)

    def testMustHaveWrite(self):
        related_info_id = self._create_initial_entry()['id']
        self.acl.canWrite = False
        self.acl.save()
        response = self.client.delete(\
                    reverse('tardis.apps.related_info.views.'\
                            +'get_or_update_or_delete_related_info',
                            args=[self.experiment.id, related_info_id]))
        expect(response.status_code).to_equal(403)

    def testCanDelete(self):
        response = self.client.delete(\
                    reverse('tardis.apps.related_info.views.'\
                            +'get_or_update_or_delete_related_info',
                            args=[self.experiment.id,
                                  self._create_initial_entry()['id']]))
        expect(response.status_code).to_equal(200)
        obj = json.loads(response.content)
        expect(obj.keys()).to_be_greater_than(1)
