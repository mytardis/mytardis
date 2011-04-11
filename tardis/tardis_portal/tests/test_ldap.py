"""

.. moduleauthor:: Ruseell Sim <russell.sim@monash.edu>
"""
from django.test import TestCase
from nose.plugins.skip import SkipTest
server = None


class LDAPErrorTest(TestCase):

    def test_search(self):
        from tardis.tardis_portal.auth.ldap_auth import ldap_auth
        l = ldap_auth()
        self.assertEqual(l._query('', '', ''), None)


class LDAPTest(TestCase):
    def setUp(self):
        from tardis.tardis_portal.tests.ldap_ldif import test_ldif
        import slapd
        global server
        if not slapd.Slapd.check_paths():
            raise SkipTest()

        server = slapd.Slapd()
        server.set_port(38911)
        server.set_dn_suffix("dc=example, dc=com")
        server.start()
        base = server.get_dn_suffix()

        server.ldapadd("\n".join(test_ldif) + "\n")

        self.server = server

    def tearDown(self):
        self.server.stop()

    def test_search(self):
        from django.conf import settings
        from tardis.tardis_portal.auth.ldap_auth import ldap_auth

        l = ldap_auth()
        res = l._query(settings.LDAP_USER_BASE, '(objectClass=*)', ['cn'])
        res1 = [('ou=People,dc=example,dc=com', {}),
                ('uid=testuser1,ou=People,dc=example,dc=com',
                 {'cn': ['Test User']}),
                ('uid=testuser2,ou=People,dc=example,dc=com',
                 {'cn': ['Test User2']}),
                ('uid=testuser3,ou=People,dc=example,dc=com',
                 {'cn': ['Test User3']})]
        self.assertEqual(res, res1)

        res = l._query(settings.LDAP_GROUP_BASE, '(objectClass=*)', ['cn'])
        res1 = [('ou=Group,dc=example,dc=com', {}),
                ('cn=empty,ou=Group,dc=example,dc=com',
                 {'cn': ['empty']}),
                ('cn=full,ou=Group,dc=example,dc=com',
                 {'cn': ['full']}),
                ('cn=systems,ou=Group,dc=example,dc=com',
                 {'cn': ['systems']})]
        self.assertEqual(res, res1)

    def test_getuserbyid(self):
        from tardis.tardis_portal.auth.ldap_auth import ldap_auth
        l = ldap_auth()
        user = l.getUserById('testuser1')
        user1 = {'id': 'testuser1',
                 'email': 't.user@example.com',
                 'display': 'Test'}
        self.assertEqual(user, user1)

        user = l.getUserById('nulluser')
        self.assertEqual(user, None)

    def test_authenticate(self):
        from tardis.tardis_portal.auth.ldap_auth import ldap_auth
        from django.core.handlers.wsgi import WSGIRequest
        from django.contrib.auth.models import User

        # Tests Authenticate API
        l = ldap_auth()
        req = WSGIRequest({"REQUEST_METHOD": "POST"})
        req._post = {'username': 'testuser1',
                     'password': 'kklk',
                     'authMethod': 'ldap'}
        u = l.authenticate(req)
        u1 = {'email': 't.user@example.com',
              'display': 'Test', 'id': 'testuser1'}
        self.failUnlessEqual(u, u1)

        # Test authservice API
        from tardis.tardis_portal.auth import auth_service
        req = WSGIRequest({"REQUEST_METHOD": "POST"})
        req._post = {'username': 'testuser1',
                     'password': 'kklk',
                     'authMethod': 'ldap'}
        user = auth_service.authenticate('ldap', request=req)
        self.assertTrue(isinstance(user, User))

        # Check that there is an entry in the user authentication table
        from tardis.tardis_portal.models import UserAuthentication
        userAuth = UserAuthentication.objects.get(
            userProfile__user=user,
            authenticationMethod=l.name)

        user1 = UserAuthentication.objects.get(username=user.username,
                        authenticationMethod='ldap').userProfile.user
        self.assertEqual(user, user1)

    def test_getgroups(self):
        from django.contrib.auth.models import User
        from django.core.handlers.wsgi import WSGIRequest
        from tardis.tardis_portal.auth import auth_service
        req = WSGIRequest({"REQUEST_METHOD": "POST"})
        req._post = {'username': 'testuser1',
                     'password': 'kklk',
                     'authMethod': 'ldap'}
        user = auth_service.authenticate('ldap', request=req)
        self.assertTrue(isinstance(user, User))
        req.user = user

        from tardis.tardis_portal.auth.ldap_auth import ldap_auth
        # Tests getGroups
        l = ldap_auth()
        self.assertEqual([g for g in l.getGroups(req)], ['full', 'systems'])

    def test_getgroupbyid(self):
        from tardis.tardis_portal.auth.ldap_auth import ldap_auth
        l = ldap_auth()
        self.assertEqual(l.getGroupById('full'),
                         {'id': 'full', 'display': 'Full Group'})
        self.assertEqual(l.getGroupById('invalid'), None)

    def test_getgroupsforentity(self):
        from tardis.tardis_portal.auth.ldap_auth import ldap_auth
        l = ldap_auth()
        self.assertEqual([g for g in l.getGroupsForEntity('testuser1')],
                         [{'id': 'full', 'display': 'Full Group'},
                          {'id': 'systems', 'display': 'Systems Services'}])

    def test_searchgroups(self):
        from tardis.tardis_portal.auth.ldap_auth import ldap_auth
        l = ldap_auth()
        self.assertEqual([g for g in l.searchGroups(id='fu*')],
                         [{'id': 'full',
                           'members': ['testuser1', 'testuser2', 'testuser3'],
                           'display': 'Full Group'}])
