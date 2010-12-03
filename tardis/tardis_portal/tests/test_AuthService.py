
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY

from tardis.tardis_portal.auth import AuthProvider, UserProvider, GroupProvider


class MockSettings(object):
    pass


class MockGroupProvider(GroupProvider):
    def __init__(self):
        self.name = u'mockdb'
        self.groups = {u'1': {"display": "Group 123",
                             "members": [u'user1', u'user2']},
                       u'2': {"display": 'Group 456',
                             'members': [u'user1', u'user3']},
                       }

    def getGroups(self, request):
        for k, v in self.groups.items():
            if str(request.user) in v['members']:
                yield k

    def getGroupById(self, id):
        return self.group[id]

    def searchGroups(self, filter):
        pass

    def getGroupsForEntity(self, id):
        pass


class AuthServiceTestCase(TestCase):
    urls = 'tardis.tardis_portal.tests.urls'

    def setUp(self):
        from django.contrib.auth.models import User
        self.user1 = User.objects.create_user('user1', '', 'secret')
        self.user2 = User.objects.create_user('user2', '', 'secret')
        self.user3 = User.objects.create_user('user3', '', 'secret')

    def testInitialisation(self):
        from tardis.tardis_portal.auth import AuthService
        s = MockSettings()
        s.USER_PROVIDERS = ()
        s.GROUP_PROVIDERS = ()
        a = AuthService(settings=s)

        s.USER_PROVIDERS = ('tardis.tardis_portal.auth.localdb_auth.DjangoUserProvider',)
        s.GROUP_PROVIDERS = ('tardis.tardis_portal.auth.localdb_auth.DjangoGroupProvider',)
        a = AuthService(settings=s)
        self.assertEqual(len(a._user_providers), 1)
        self.assertEqual(len(a._group_providers), 1)

    def testGroupProvider(self):
        from tardis.tardis_portal.auth import AuthService, auth_service
        s = MockSettings()
        s.USER_PROVIDERS = ()
        s.GROUP_PROVIDERS = ('tardis.tardis_portal.tests.test_AuthService.MockGroupProvider',)
        a = AuthService(settings=s)
        self.assertEqual(len(a._group_providers), 1)

        # add the local group provider to the singleton auth_service
        auth_service._group_providers = a._group_providers

        c = Client()
        c.login(username='user1', password='secret')
        self.assert_(SESSION_KEY in c.session)

        r = str(c.get('/groups/'))
        self.assertEqual(r.count('mockdb'), 2)
        self.assertTrue('1' in r)
        self.assertTrue('2' in r)

        c.login(username='user2', password='secret')
        self.assert_(SESSION_KEY in c.session)

        r = str(c.get('/groups/'))
        self.assertEqual(r.count('mockdb'), 1, r)
        self.assertTrue('1' in r)
