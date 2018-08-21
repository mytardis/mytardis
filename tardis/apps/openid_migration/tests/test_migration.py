'''
Tests related to OpenID migration

'''

import json

from django.test import TestCase
from django.test.client import Client
from django.http import HttpRequest, QueryDict
from django.contrib.auth.models import User, Group

from tardis.tardis_portal.models import Experiment, ObjectACL
from tardis.tardis_portal.models import UserAuthentication, UserProfile

from ..migration import do_migration


class OpenIDMigrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # old_user
        user_old_username = 'tardis_user1'
        # new_user
        user_new_username = 'tardis_user2'
        pwd = 'secret'
        email = 'tadis@tardis.com'
        self.user_new = User.objects.create_user(user_new_username, email, pwd)
        self.user_old = User.objects.create_user(user_old_username, email, pwd)
        # create group
        self.group = Group.objects.create(name='test group')
        # add old user to group
        self.group.user_set.add(self.user_old)
        # add user auth
        user_auth = UserAuthentication(userProfile=UserProfile.objects.get(user=self.user_old),
                           username= self.user_old.username,
                           authenticationMethod='localdb')
        user_auth.save()
        # add experiments
        experiment = Experiment(title='Text Experiment',
                                institution_name='Test Uni',
                                created_by=self.user_old)
        experiment.save()
        acl = ObjectACL(
            pluginId='django_user',
            entityId=str(self.user_old.id),
            content_object=experiment,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED,
        )
        acl.save()

    def test_do_migration(self):
        from django.contrib.messages.storage.fallback import FallbackStorage
        data = [('username', self.user_old.username), ('password', 'secret'),
                ('operation', u'migrateAccount')]
        post = QueryDict('&'.join(['%s=%s' % (k, v) for (k, v) in
                                   data]))
        request = HttpRequest()
        request.session = dict(_auth_user_backend='tardis.tardis_portal.auth.localdb_auth.DjangoAuthBackend')
        request.POST = post
        request.user = self.user_new
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        response = do_migration(request)
        d = json.loads(response.content)
        self.assertEqual(d['status'], 'success')
