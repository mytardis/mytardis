"""
test_auth_views.py

Tests for view methods relating to users, groups, access controls
and authorization

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
import json
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from ...models import Experiment, ExperimentACL


class UserGroupListsTestCase(TestCase):
    def setUp(self):
        from django.conf import settings

        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)

        self.accounts = [
            ("user1", "pwd1", "useronefirstname", "useronelastname"),
            ("user2", "pwd2", "usertwofirstname", "usertwolastname"),
            ("user3", "pwd3", "userthreefirstname", "userthreelastname"),
        ]

        for (uname, pwd, first, last) in self.accounts:
            user = User.objects.create_user(uname, "", pwd)
            user.first_name = first
            user.last_name = last
            user.save()
        self.users = User.objects.all().exclude(pk=settings.PUBLIC_USER_ID)

        self.client = Client()
        login = self.client.login(
            username=self.accounts[0][0], password=self.accounts[0][1]
        )
        self.assertTrue(login)

        self.groups = ["group1", "group2", "group3", "group4"]
        for groupname in self.groups:
            group = Group(name=groupname)
            group.save()

    def test_get_user_list(self):

        # Match all
        response = self.client.get("/ajax/user_list/?q=")
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content.decode())
        self.assertTrue(len(users_dict) == self.users.count())
        for user in self.users:
            user_info = [u for u in users_dict if u["username"] == user.username]
            self.assertTrue(len(user_info) == 1)
            self.assertTrue(user_info[0]["first_name"] == user.first_name)
            self.assertTrue(user_info[0]["last_name"] == user.last_name)

        # Match on first name
        response = self.client.get("/ajax/user_list/?q=threefirst")
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content.decode())

        self.assertTrue(len(users_dict) == 1)
        acct = self.users.get(username="user3")
        self.assertTrue(users_dict[0]["username"] == acct.username)
        self.assertTrue(users_dict[0]["first_name"] == acct.first_name)
        self.assertTrue(users_dict[0]["last_name"] == acct.last_name)

        # Match on last name
        response = self.client.get("/ajax/user_list/?q=twolast")
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content.decode())

        self.assertTrue(len(users_dict) == 1)
        acct = self.users.get(username="user2")
        self.assertTrue(users_dict[0]["username"] == acct.username)
        self.assertTrue(users_dict[0]["first_name"] == acct.first_name)
        self.assertTrue(users_dict[0]["last_name"] == acct.last_name)

        # Case insensitive matching
        response = self.client.get("/ajax/user_list/?q=TWOFIRSTNAME")
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content.decode())
        self.assertTrue(len(users_dict) == 1)
        acct = self.users.get(username="user2")
        self.assertTrue(users_dict[0]["username"] == acct.username)

        # Partial match on "first_name last_name"
        response = self.client.get("/ajax/user_list/?q=onefirstname useronelast")
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content.decode())
        self.assertTrue(len(users_dict) == 1)
        self.assertTrue(users_dict[0]["username"] == "user1")

    def test_get_group_list(self):

        response = self.client.get("/ajax/group_list/")
        self.assertEqual(response.status_code, 200)
        ret_names = response.content.decode().split(" ~ ")
        self.assertTrue(len(ret_names) == Group.objects.count())

        for (group_name, ret_name) in zip(self.groups, ret_names):
            self.assertEqual(group_name, ret_name)

    def tearDown(self):
        self.client.logout()


class UserListTestCase(TestCase):
    """
    User lists are used for autocompleting the user-to-share-with
    field when granting access to an experiment
    """

    def setUp(self):
        from django.conf import settings

        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        self.accounts = [
            ("user1", "pwd1", "useronefirstname", "useronelastname"),
            ("user2", "pwd2", "usertwofirstname", "usertwolastname"),
            ("user3", "pwd3", "userthreefirstname", "userthreelastname"),
        ]

        for (uname, pwd, first, last) in self.accounts:
            user = User.objects.create_user(uname, "", pwd)
            user.first_name = first
            user.last_name = last
            user.save()
        self.users = User.objects.all().exclude(pk=settings.PUBLIC_USER_ID)

        self.client = Client()
        login = self.client.login(
            username=self.accounts[0][0], password=self.accounts[0][1]
        )
        self.assertTrue(login)

    def test_get_user_list(self):

        # Match all
        response = self.client.get("/ajax/user_list/?q=")
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content.decode())
        self.assertEqual(len(self.users), len(users_dict))
        for user in self.users:
            user_info = [u for u in users_dict if u["username"] == user.username]
            self.assertEqual(1, len(user_info))
            self.assertEqual(user_info[0]["first_name"], user.first_name)
            self.assertEqual(user_info[0]["last_name"], user.last_name)

        # Match on last name
        response = self.client.get("/ajax/user_list/?q=useronelastname")
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content.decode())

        self.assertEqual(len(users_dict), 1)

    def tearDown(self):
        self.client.logout()


class RightsTestCase(TestCase):
    def test_rights_require_valid_owner(self):
        # Create test owner without enough details
        username, email, password = ("testuser", "testuser@example.test", "password")
        user = User.objects.create_user(username, email, password)

        # Create test experiment and make user the owner of it
        experiment = Experiment(
            title="Text Experiment", institution_name="Test Uni", created_by=user
        )
        experiment.save()
        acl = ExperimentACL(
            user=user,
            experiment=experiment,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        acl.save()

        # Create client and login as user
        client = Client()
        login = client.login(username=username, password=password)
        self.assertTrue(login)

        # Get "Choose Rights" page, and check that we're forbidden
        rights_url = reverse(
            "tardis.tardis_portal.views.choose_rights", args=[str(experiment.id)]
        )
        response = client.get(rights_url)
        self.assertEqual(response.status_code, 403)

        # Fill in remaining details
        user.first_name = "Voltaire"  # Mononymous persons are just fine
        user.save()

        # Get "Choose Rights" page, and check that we're now allowed access
        response = client.get(rights_url)
        self.assertEqual(response.status_code, 200)


class ManageAccountTestCase(TestCase):
    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_manage_account(self, mock_webpack_get_bundle):
        # Create test owner without enough details
        username, email, password = ("testuser", "testuser@example.test", "password")
        user = User.objects.create_user(username, email, password)
        self.assertFalse(user.userprofile.isValidPublicContact())

        manage_url = reverse("tardis.tardis_portal.views.manage_user_account")

        # Create client and go to account management URL
        client = Client()
        response = client.get(manage_url)
        # Expect redirect to login
        self.assertEqual(response.status_code, 302)

        # Login as user
        login = client.login(username=username, password=password)
        self.assertTrue(login)

        response = client.get(manage_url)
        # Expect 200 OK and a form
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)
        response.content.index(b'name="first_name"')
        response.content.index(b'name="last_name"')
        response.content.index(b'name="email"')
        response.content.index(b'value="testuser@example.test"')

        # Update account details
        response = client.post(
            manage_url, {"first_name": "Tommy", "email": "tommy@atkins.net"}
        )
        # Expect 303 See Also redirect on update
        self.assertEqual(response.status_code, 303)

        user = User.objects.get(id=user.id)
        self.assertTrue(user.userprofile.isValidPublicContact())
