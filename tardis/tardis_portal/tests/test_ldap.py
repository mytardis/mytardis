"""

.. moduleauthor:: Russell Sim <russell.sim@monash.edu>
"""
from unittest import skip, skipIf

from django.conf import settings
from django.test import RequestFactory, TestCase

# from nose.plugins.skip import SkipTest

server = None

ldap_auth_provider = ("ldap", "LDAP", "tardis.tardis_portal.auth.ldap_auth.ldap_auth")


@skipIf(
    ldap_auth_provider not in settings.AUTH_PROVIDERS,
    "ldap_auth is not enabled, skipping tests",
)
class LDAPErrorTest(TestCase):
    def test_search(self):
        from ..auth.ldap_auth import ldap_auth

        l = ldap_auth(force_create=True)
        self.assertEqual(l._query("", "", []), None)


# this test might still skip if SlapD.check_paths() is False
# see below..
@skipIf(
    ldap_auth_provider not in settings.AUTH_PROVIDERS,
    "ldap_auth is not enabled, skipping tests",
)
@skip("Incompatible with Pytest")
class LDAPTest(TestCase):
    def setUp(self):
        from . import slapd
        from .ldap_ldif import test_ldif

        global server
        # if not slapd.Slapd.check_paths():
        #    raise SkipTest('slapd.Slapd.check_paths() failed, '
        #                   'so skipping LDAPTest')

        server = slapd.Slapd()
        server.set_dn_suffix("dc=example, dc=com")
        server.start()
        settings.LDAP_URL = server.get_url()
        dummy_base = server.get_dn_suffix()

        server.ldapadd("\n".join(test_ldif) + "\n")

        self.server = server

    def tearDown(self):
        self.server.stop()

    def test_search(self):
        from django.conf import settings

        from ..auth.ldap_auth import ldap_auth

        l = ldap_auth(force_create=True)
        res = l._query(settings.LDAP_USER_BASE, "(objectClass=*)", ["givenName", "sn"])
        res1 = [
            ("ou=People,dc=example,dc=com", {}),
            (
                "uid=testuser1,ou=People,dc=example,dc=com",
                {"givenName": [b"Test"], "sn": [b"User"]},
            ),
            (
                "uid=testuser2,ou=People,dc=example,dc=com",
                {"givenName": [b"Test"], "sn": [b"User2"]},
            ),
            (
                "uid=testuser3,ou=People,dc=example,dc=com",
                {"givenName": [b"Test"], "sn": [b"User3"]},
            ),
        ]
        self.assertEqual(res, res1)

        res = l._query(settings.LDAP_GROUP_BASE, "(objectClass=*)", ["cn"])
        res1 = [
            ("ou=Group,dc=example,dc=com", {}),
            ("cn=empty,ou=Group,dc=example,dc=com", {"cn": [b"empty"]}),
            ("cn=full,ou=Group,dc=example,dc=com", {"cn": [b"full"]}),
            ("cn=systems,ou=Group,dc=example,dc=com", {"cn": [b"systems"]}),
        ]
        self.assertEqual(res, res1)

    def test_getuserbyid(self):
        from ..auth.ldap_auth import ldap_auth

        l = ldap_auth(force_create=True)
        user = l.getUserById("testuser1")
        user1 = {
            "id": "testuser1",
            "email": "t.user@example.com",
            "first_name": "Test",
            "last_name": "User",
        }
        self.assertEqual(user, user1)

        user = l.getUserById("nulluser")
        self.assertEqual(user, None)

    def test_authenticate(self):
        from django.contrib.auth.models import User

        from ..auth.ldap_auth import ldap_auth

        # Tests Authenticate API
        l = ldap_auth(force_create=True)
        rf = RequestFactory()
        req = rf.post("")
        req._post = {"username": "testuser1", "password": "kklk", "authMethod": "ldap"}
        u = l.authenticate(req)
        u1 = {
            "email": "t.user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "id": "testuser1",
        }
        self.assertEqual(u, u1)

        # Test authservice API
        from ..auth.authservice import AuthService

        auth_service = AuthService()
        req = rf.post("")
        req._post = {"username": "testuser1", "password": "kklk", "authMethod": "ldap"}
        user = auth_service.authenticate("ldap", request=req)
        self.assertIsInstance(user, User)

        # Check that there is an entry in the user authentication table
        from ..models import UserAuthentication

        UserAuthentication.objects.get(
            userProfile__user=user, authenticationMethod=l.name
        )

        user1 = UserAuthentication.objects.get(
            username=user.username, authenticationMethod="ldap"
        ).userProfile.user
        self.assertEqual(user, user1)

    def test_getgroups(self):
        from django.contrib.auth.models import User

        from ..auth.authservice import AuthService
        from ..auth.ldap_auth import ldap_auth

        l = ldap_auth(force_create=True)
        auth_service = AuthService()
        rf = RequestFactory()
        req = rf.post("")
        req._post = {"username": "testuser1", "password": "kklk", "authMethod": "ldap"}
        user = auth_service.authenticate("ldap", request=req)
        self.assertIsInstance(user, User)
        req.user = user

        # Tests getGroups
        self.assertEqual(list(l.getGroups(req.user)), ["full", "systems"])

    def test_getgroupbyid(self):
        from ..auth.ldap_auth import ldap_auth

        l = ldap_auth(force_create=True)
        self.assertEqual(
            l.getGroupById("full"), {"id": "full", "display": "Full Group"}
        )
        self.assertEqual(l.getGroupById("invalid"), None)

    def test_getgroupsforentity(self):
        from ..auth.ldap_auth import ldap_auth

        l = ldap_auth(force_create=True)
        self.assertEqual(
            list(l.getGroupsForEntity("testuser1")),
            [
                {"id": "full", "display": "Full Group"},
                {"id": "systems", "display": "Systems Services"},
            ],
        )

    def test_searchgroups(self):
        from ..auth.ldap_auth import ldap_auth

        l = ldap_auth(force_create=True)
        self.assertEqual(
            list(l.searchGroups(id="fu*")),
            [
                {
                    "id": "full",
                    "members": ["testuser1", "testuser2", "testuser3"],
                    "display": "Full Group",
                }
            ],
        )
