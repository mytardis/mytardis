import json
import re
import six

from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from django.urls import reverse

from tardis.tardis_portal.models import Experiment, ObjectACL, User
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager


def _create_user_and_login(username='testuser', password='testpass'):
    user = User.objects.create_user(username, '', password)
    user.save()

    client = Client()
    client.login(username=username, password=password)
    return user, client


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
        response = client.get(
            reverse('tardis.apps.related_info.views.index',
                    args=[self.experiment.id]))
        self.assertEqual(response.status_code, 403)

    def testAccessWithReadPerms(self):
        response = self.client.get(
            reverse('tardis.apps.related_info.views.index',
                    args=[self.experiment.id]))
        self.assertEqual(response.status_code, 200)


class ListTestCase(TransactionTestCase):

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
        response = self.client.get(
            reverse('tardis.apps.related_info.views.'
                    + 'list_or_create_related_info',
                    args=[self.experiment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEqual(response.content, '[]')

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

        response = self.client.get(
            reverse('tardis.apps.related_info.views.' +
                    'list_or_create_related_info',
                    args=[self.experiment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'], 'application/json; charset=utf-8')

        objs = json.loads(response.content)
        self.assertEqual(len(objs), 1)
        for k, v in params.items():
            self.assertEqual(objs[0][k], v)

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

        response = self.client.get(
            reverse('tardis.apps.related_info.views.'
                    + 'list_or_create_related_info',
                    args=[self.experiment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'], 'application/json; charset=utf-8')

        objs = json.loads(response.content)
        self.assertEqual(len(objs), 10)

        for obj in objs:
            self.assertEqual(obj['type'], 'website')
            six.assertRegex(
                self,
                obj['identifier'], r'www.example.test/\d+$', obj['identifier'])
            six.assertRegex(self, obj['title'], r'^Title #\d+$')
            six.assertRegex(self, obj['notes'], r'note #\d+\.$')


class GetTestCase(TransactionTestCase):

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
        response = self.client.get(
            reverse('tardis.apps.related_info.views.' +
                    'get_or_update_or_delete_related_info',
                    args=[self.experiment.id, 0]))
        self.assertEqual(response.status_code, 404)

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

        response = self.client.get(
            reverse('tardis.apps.related_info.views.' +
                    'get_or_update_or_delete_related_info',
                    args=[self.experiment.id, psm.parameterset.id]))
        self.assertEqual(response.status_code, 200)

        obj = json.loads(response.content)
        for k, v in params.items():
            self.assertEqual(obj[k], v)


class CreateTestCase(TransactionTestCase):

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
        response = self.client.post(
            reverse('tardis.apps.related_info.views.'
                    + 'list_or_create_related_info',
                    args=[self.experiment.id]),
            data=json.dumps(params),
            content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def testCanCreate(self):
        params = {'type': 'website',
                  'identifier': 'https://www.google.com/',
                  'title': 'Google',
                  'notes': 'This is a note.'}
        response = self.client.post(
            reverse('tardis.apps.related_info.views.'
                    + 'list_or_create_related_info',
                    args=[self.experiment.id]),
            data=json.dumps(params),
            content_type='application/json')
        # Check that content reports as created, returns the created object
        self.assertEqual(response.status_code, 201)
        obj = json.loads(response.content)
        self.assertIsInstance(
            obj['id'], int, 'Created object should have an ID.')
        for k, v in params.items():
            self.assertEqual(obj[k], v)
        # Check that creation really did persist
        response = self.client.get(
            reverse('tardis.apps.related_info.views.'
                    + 'get_or_update_or_delete_related_info',
                    args=[self.experiment.id, obj['id']]))
        self.assertEqual(response.status_code, 200)

    def testDetectsBadInput(self):
        def do_post(params):
            return self.client.post(
                reverse('tardis.apps.related_info.views.'
                        + 'list_or_create_related_info',
                        args=[self.experiment.id]),
                data=json.dumps(params),
                content_type='application/json')
        # We need an identifier
        params = {'type': 'website'}
        response = do_post(params)
        self.assertEqual(response.status_code, 400)
        # We need a type
        params = {'identifier': 'http://www.google.com/'}
        response = do_post(params)
        self.assertEqual(response.status_code, 400)
        # We need an identifier and URL
        params = {'type': 'website', 'identifier': 'http://www.google.com/'}
        response = do_post(params)
        self.assertEqual(response.status_code, 201)


class UpdateTestCase(TransactionTestCase):

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
        response = self.client.post(reverse('tardis.apps.related_info.views.' +
                                            'list_or_create_related_info',
                                            args=[self.experiment.id]),
                                    data=json.dumps(params),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        return json.loads(response.content)

    def testMustHaveWrite(self):
        related_info_id = self._create_initial_entry()['id']
        self.acl.canWrite = False
        self.acl.save()
        params = {'type': 'website',
                  'identifier': 'https://www.google.com/'}
        response = self.client.put(
            reverse('tardis.apps.related_info.views.' +
                    'get_or_update_or_delete_related_info',
                    args=[self.experiment.id, related_info_id]),
            data=json.dumps(params),
            content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def testDetectsBadInput(self):
        def do_put(params):
            return self.client.put(
                reverse('tardis.apps.related_info.views.' +
                        'get_or_update_or_delete_related_info',
                        args=[self.experiment.id,
                              self._create_initial_entry()['id']]),
                data=json.dumps(params),
                content_type='application/json')
        # We need an identifier
        params = {'type': 'website'}
        response = do_put(params)
        self.assertEqual(response.status_code, 400)
        # We need a type
        params = {'identifier': 'http://www.google.com/'}
        response = do_put(params)
        self.assertEqual(response.status_code, 400)
        # We need an identifier and URL
        params = {'type': 'website',
                  'identifier': 'http://www.google.com/'}
        response = do_put(params)
        self.assertEqual(response.status_code, 201)


class DeleteTestCase(TransactionTestCase):

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
        response = self.client.post(reverse('tardis.apps.related_info.views.' +
                                            'list_or_create_related_info',
                                            args=[self.experiment.id]),
                                    data=json.dumps(params),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        return json.loads(response.content)

    def testMustHaveWrite(self):
        related_info_id = self._create_initial_entry()['id']
        self.acl.canWrite = False
        self.acl.save()
        response = self.client.delete(
            reverse('tardis.apps.related_info.views.' +
                    'get_or_update_or_delete_related_info',
                    args=[self.experiment.id, related_info_id]))
        self.assertEqual(response.status_code, 403)

    def testCanDelete(self):
        response = self.client.delete(
            reverse('tardis.apps.related_info.views.' +
                    'get_or_update_or_delete_related_info',
                    args=[self.experiment.id,
                          self._create_initial_entry()['id']]))
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertGreater(obj.keys(), 1)
