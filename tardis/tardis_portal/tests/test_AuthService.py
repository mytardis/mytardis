
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY

from tardis.tardis_portal.auth import AuthProvider, UserProvider, GroupProvider


class MockSettings(object):
    def __init__(self):
        self.AUTH_PROVIDERS = ()
        self.USER_PROVIDERS = ()
        self.GROUP_PROVIDERS = ()


class MockGroupProvider(GroupProvider):
    def __init__(self):
        self.name = u'mockdb'
        self.groups = [{"name": "Group 456", 'id': '2',
                        "members": [u'user1', u'user3']},
                       {"name": 'Group 123', 'id': '1',
                        'members': [u'user1', u'user2']},
                       {"name": 'Super Group', 'id': '3',
                        'members': [u'Group 123', u'user2']},
                       ]

    def getGroups(self, request):
        for i in self.groups:
            if str(request.user) in i['members']:
                yield i['id']

    def getGroupById(self, id):
        pass

    def searchGroups(self, **filter):
        for g in self.groups:
            for s, t in filter.items():
                if not s in g:
                    continue
                if t in g[s]:
                    group = g.copy()
                    del group['members']
                    yield group

    def getGroupsForEntity(self, id):
        for g in self.groups:
            if not id in g['members']:
                continue
            group = g.copy()
            del group['members']
            yield group


class AuthServiceTestCase(TestCase):
    urls = 'tardis.tardis_portal.tests.urls'

    def setUp(self):
        from django.contrib.auth.models import User
        self.user1 = User.objects.create_user('user1', '', 'secret')
        self.user2 = User.objects.create_user('user2', '', 'secret')
        self.user3 = User.objects.create_user('user3', '', 'secret')

        from tardis.tardis_portal.auth import AuthService, auth_service
        s = MockSettings()
        s.GROUP_PROVIDERS = \
            ('tardis.tardis_portal.tests.test_AuthService.MockGroupProvider',)
        a = AuthService(settings=s)

        self._auth_service_group_providers = auth_service._group_providers
        # add the local group provider to the singleton auth_service
        auth_service._group_providers = a._group_providers

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()

        from tardis.tardis_portal.auth import auth_service
        auth_service._group_providers = self._auth_service_group_providers

    def testInitialisation(self):
        from tardis.tardis_portal.auth import AuthService
        s = MockSettings()
        a = AuthService(settings=s)

        s.USER_PROVIDERS = \
            ('tardis.tardis_portal.auth.localdb_auth.DjangoUserProvider',)
        s.GROUP_PROVIDERS = \
            ('tardis.tardis_portal.auth.localdb_auth.DjangoGroupProvider',)
        a = AuthService(settings=s)
        self.assertEqual(len(a._user_providers), 1)
        self.assertEqual(len(a._group_providers), 1)

    def testGroupProvider(self):
        from tardis.tardis_portal.auth import AuthService
        s = MockSettings()
        s.GROUP_PROVIDERS = \
            ('tardis.tardis_portal.tests.test_AuthService.MockGroupProvider',)
        a = AuthService(settings=s)
        self.assertEqual(len(a._group_providers), 1)

        c = Client()
        c.login(username='user1', password='secret')
        self.assert_(SESSION_KEY in c.session)

        r = str(c.get('/test/groups/'))
        self.assertEqual(r.count('mockdb'), 2)
        self.assertTrue(',1)' in r)
        self.assertTrue(',2)' in r)

        c.login(username='user2', password='secret')
        self.assert_(SESSION_KEY in c.session)

        r = str(c.get('/test/groups/'))
        self.assertEqual(r.count('mockdb'), 2, r)
        self.assertTrue(',1)' in r)
        self.assertTrue(',3)' in r)

    def testGroupSearch(self):
        from tardis.tardis_portal.auth import AuthService
        s = MockSettings()
        s.GROUP_PROVIDERS = \
            ('tardis.tardis_portal.tests.test_AuthService.MockGroupProvider',)
        a = AuthService(settings=s)

        # check the correct group provider is registered
        self.assertEqual(len(a._group_providers), 1)

        # test searching for groups by substring
        self.assertEqual(len(a.searchGroups(name='Group')), 3)
        self.assertEqual(len(a.searchGroups(name='123')), 1)
        self.assertEqual(a.searchGroups(name='123')[0]['id'], '1')
        self.assertEqual(a.searchGroups(name='123')[0]['pluginname'], 'mockdb')

        # test limiting the number of results
        self.assertEqual(len(a.searchGroups(name='Group', max_results=1)), 1)

        # test sorting the result
        self.assertEqual(a.searchGroups(name='Group', sort_by='name')[0]['id'],
                         '1')

    def testGetGroupsForEntity(self):
        from tardis.tardis_portal.auth import AuthService
        s = MockSettings()
        s.GROUP_PROVIDERS = \
            ('tardis.tardis_portal.tests.test_AuthService.MockGroupProvider',)
        a = AuthService(settings=s)

        # check the correct group provider is registered
        self.assertEqual(len(a._group_providers), 1)

        self.assertEqual(len([g for g in a.getGroupsForEntity('user1')]), 2)
        self.assertEqual(len([g for g in a.getGroupsForEntity('Group 123')]), 1)

    def testAuthenticate(self):
        from tardis.tardis_portal.auth import AuthService
        s = MockSettings()
        s.USER_PROVIDERS = ()
        s.GROUP_PROVIDERS = ()
        a = AuthService(settings=s)

        pass
