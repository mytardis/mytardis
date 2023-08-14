"""
test_project_views.py

Tests for view methods relating to projects

.. moduleauthor::  Mike Laverick <mike.laverick@auckland.ac.nz>

"""
# import json
from unittest import skipIf
from unittest.mock import patch
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.test.client import Client
from django.urls import resolve, reverse

from ...models import Project, ProjectACL, Institution


@skipIf(settings.ONLY_EXPERIMENT_ACLS is True, "skipping Micro ACL specific test")
class ProjectTestCase(TestCase):
    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        # Create test owner without enough details
        username, email, password = ("testuser", "testuser@example.test", "password")
        user = User.objects.create_user(username, email, password)
        for perm in ("add_project", "change_project"):
            user.user_permissions.add(Permission.objects.get(codename=perm))
        user.save()
        # Data used in tests
        self.user, self.username, self.password = (user, username, password)
        self.userprofile = self.user.userprofile

        self.institution = Institution.objects.create(name="University of Auckland")
        self.institution.save()

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_create_and_edit(self, mock_webpack_get_bundle):
        # Login as user
        client = Client()
        login = client.login(username=self.username, password=self.password)
        self.assertTrue(login)

        ##########
        # Create #
        ##########

        create_url = reverse("tardis.apps.projects.create_project")
        # Check the form is accessible
        response = client.get(create_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # Create client and go to account management URL
        data = {
            "name": "The Elements",
            "principal_investigator": str(self.user.id),
            "institution": str(self.institution.id),
            "description": "There's antimony, arsenic, aluminum, selenium,"
            + "And hydrogen and oxygen and nitrogen and rhenium...",
        }
        response = client.post(create_url, data=data)
        # Expect redirect to created project
        self.assertEqual(response.status_code, 303)
        created_url = response["Location"]

        # Check that it redirects to a valid location
        response = client.get(created_url)
        self.assertEqual(response.status_code, 200)

        project_id = resolve(urlparse(created_url).path).kwargs["project_id"]
        project = Project.objects.get(id=project_id)
        for attr in (
            "name",
            "description",
        ):
            self.assertEqual(getattr(project, attr), data[attr])
        self.assertEqual(
            str(getattr(project, "principal_investigator_id")),
            data["principal_investigator"],
        )
        # Check institutions were created properly
        self.assertEqual(
            [str(a.id) for a in project.institution.all()],
            data["institution"].split(", "),
        )

        acl = ProjectACL.objects.get(project=project, user=self.user)
        self.assertTrue(acl.canRead)
        self.assertTrue(acl.canWrite)
        self.assertTrue(acl.isOwner)

        ########
        # Edit #
        ########

        edit_url = reverse(
            "tardis.apps.projects.edit_project",
            kwargs={"project_id": str(project_id)},
        )

        # Check the form is accessible
        response = client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        # Create client and go to account management URL
        data = {
            "name": "I Am the Very Model of a Modern Major-General",
            "principal_investigator": str(self.user.id),
            "institution": str(self.institution.id),
            "description": "I am the very model of a modern Major-General,"
            + "I've information vegetable, animal, and mineral,",
        }
        response = client.post(edit_url, data=data)
        # Expect redirect to created project
        self.assertEqual(response.status_code, 303)
        edit_url = response["Location"]

        # Check that it redirects to a valid location
        response = client.get(created_url)
        self.assertEqual(response.status_code, 200)

        project_id = resolve(urlparse(created_url).path).kwargs["project_id"]
        project = Project.objects.get(id=project_id)
        for attr in ("name", "description"):
            self.assertEqual(getattr(project, attr), data[attr])
        self.assertEqual(
            str(getattr(project, "principal_investigator_id")),
            data["principal_investigator"],
        )
        # Check institutions were created properly
        self.assertEqual(
            [str(a.id) for a in project.institution.all()],
            data["institution"].split(", "),
        )
