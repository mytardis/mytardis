
from django.test import TestCase


class MockSettings(object):
    pass


class AuthSeriveTestCase(TestCase):

    def setUp(self):
        pass

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
