# -*- coding: utf-8 -*-
from django.contrib.auth import SESSION_KEY
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

from ..auth.interfaces import GroupProvider
from ..models import User


class MockSettings(object):
    def __init__(self):
        self.AUTH_PROVIDERS = ()
        self.USER_PROVIDERS = ()
        self.GROUP_PROVIDERS = ()


class MockGroupProvider(GroupProvider):
    def __init__(self):
        self.name = "mockdb"
        self.groups = [
            {"name": "Group 456", "id": "2", "members": ["user1", "user3"]},
            {"name": "Group 123", "id": "1", "members": ["user1", "user2"]},
            {"name": "Super Group", "id": "3", "members": ["Group 123", "user2"]},
        ]

    def getGroups(self, user):
        for i in self.groups:
            if str(user).split("_")[1] in i["members"]:
                yield i["id"]

    def getGroupById(self, id):
        pass

    def searchGroups(self, **filter):
        for g in self.groups:
            for s, t in filter.items():
                if s not in g:
                    continue
                if t in g[s]:
                    group = g.copy()
                    del group["members"]
                    yield group

    def getGroupsForEntity(self, id):
        for g in self.groups:
            if id not in g["members"]:
                continue
            group = g.copy()
            del group["members"]
            yield group


class MockRequest(HttpRequest):
    def setPost(self, field, value):
        self.POST[field] = value


class MockAuthProvider:
    def authenticate(self, request):
        username = request.POST["username"]
        username = "%s_%s" % ("mockdb", username)
        return User.objects.get(username=username)


@override_settings(ROOT_URLCONF="tardis.tardis_portal.tests.urls")
class AuthServiceTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.user1 = User.objects.create_user("mockdb_user1", "", "secret")
        self.user2 = User.objects.create_user("mockdb_user2", "", "secret")
        self.user3 = User.objects.create_user("mockdb_user3", "", "secret")

        self.userProfile1 = self.user1.userprofile
        self.userProfile2 = self.user2.userprofile
        self.userProfile3 = self.user3.userprofile

        from ..auth import AuthService, auth_service

        s = MockSettings()
        s.GROUP_PROVIDERS = (
            "tardis.tardis_portal.tests.test_authservice.MockGroupProvider",
        )
        a = AuthService(settings=s)
        a._manual_init()
        self._auth_service_group_providers = auth_service._group_providers
        # add the local group provider to the singleton auth_service
        auth_service._group_providers = a._group_providers

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()

        from ..auth import auth_service

        auth_service._group_providers = self._auth_service_group_providers
        auth_service._manual_init()

    def testInitialisation(self):
        from ..auth import AuthService

        s = MockSettings()
        s.USER_PROVIDERS = (
            "tardis.tardis_portal.auth.localdb_auth.DjangoUserProvider",
        )
        s.GROUP_PROVIDERS = (
            "tardis.tardis_portal.auth.localdb_auth.DjangoGroupProvider",
        )
        a = AuthService(settings=s)
        a._manual_init()
        self.assertEqual(len(a._user_providers), 1)
        self.assertEqual(len(a._group_providers), 1)

    def testGroupProvider(self):
        c = Client()
        login = c.login(username="mockdb_user1", password="secret")
        self.assertTrue(login)
        self.assertIn(SESSION_KEY, c.session)

        r = c.get("/test/groups/")
        self.assertEqual(r.content.count(b"mockdb"), 2)
        self.assertTrue(b",1)" in r.content)
        self.assertTrue(b",2)" in r.content)

        login = c.login(username="mockdb_user2", password="secret")
        self.assertTrue(login)
        self.assertIn(SESSION_KEY, c.session)

        r = c.get("/test/groups/")
        self.assertEqual(r.content.count(b"mockdb"), 2, r)
        self.assertTrue(b",1)" in r.content)
        self.assertTrue(b",3)" in r.content)

    def testGroupSearch(self):
        from ..auth import AuthService

        s = MockSettings()
        s.GROUP_PROVIDERS = (
            "tardis.tardis_portal.tests.test_authservice.MockGroupProvider",
        )
        a = AuthService(settings=s)
        a._manual_init()
        # check the correct group provider is registered
        self.assertEqual(len(a._group_providers), 1)

        # test searching for groups by substring
        self.assertEqual(len(a.searchGroups(name="Group")), 3)
        self.assertEqual(len(a.searchGroups(name="123")), 1)
        self.assertEqual(a.searchGroups(name="123")[0]["id"], "1")
        self.assertEqual(a.searchGroups(name="123")[0]["pluginname"], "mockdb")

        # test limiting the number of results
        self.assertEqual(len(a.searchGroups(name="Group", max_results=1)), 1)

        # test sorting the result
        self.assertEqual(a.searchGroups(name="Group", sort_by="name")[0]["id"], "1")

    def testGetGroupsForEntity(self):
        from ..auth import AuthService

        s = MockSettings()
        s.GROUP_PROVIDERS = (
            "tardis.tardis_portal.tests.test_authservice.MockGroupProvider",
        )
        a = AuthService(settings=s)
        a._manual_init()

        # check the correct group provider is registered
        self.assertEqual(len(a._group_providers), 1)

        self.assertEqual(len(list(a.getGroupsForEntity("user1"))), 2)
        self.assertEqual(len(list(a.getGroupsForEntity("Group 123"))), 1)

    def testAuthenticate(self):
        from ..auth import AuthService

        s = MockSettings()
        s.USER_PROVIDERS = ()
        s.GROUP_PROVIDERS = ()
        s.AUTH_PROVIDERS = (
            (
                "mockauth",
                "Mock Auth",
                "tardis.tardis_portal.tests.test_authservice.MockAuthProvider",
            ),
        )
        a = AuthService(settings=s)

        request = MockRequest()
        request.setPost("username", "user1")
        request.setPost("authMethod", "mockdb")

        user = a.authenticate(authMethod="mockauth", request=request)

        realUser = User.objects.get(username="mockdb_user1")
        self.assertEqual(user, realUser)
