"""
test_ajax.py

Tests for ajax view methods relating to projects

.. moduleauthor::  Mike Laverick <mike.laverick@auckland.ac.nz>

"""
from unittest import skipIf
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.test import TestCase

from tardis.tardis_portal.models import Experiment, ExperimentACL
from ...models import Project, Institution, ProjectACL


@skipIf(settings.ONLY_EXPERIMENT_ACLS is True, "skipping Micro ACL specific test")
class AjaxTestCase(TestCase):
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

        self.project = Project(
            name="Test Project 1",
            description="This is a test.",
            principal_investigator=self.user,
            created_by=self.user,
        )
        self.project.save()
        acl = ProjectACL(
            user=self.user,
            project=self.project,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ProjectACL.OWNER_OWNED,
        )
        acl.save()
        self.project.institution.add(self.institution)

        # initialise empty list to make sure they are torn down later
        self.experiments = []

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_latest_experiment(self, mock_webpack_get_bundle):
        from django.http import HttpRequest

        from tardis.apps.projects.ajax_pages import project_latest_experiment

        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        response = project_latest_experiment(request, project_id=self.project.id)
        self.assertEqual(response.status_code, 200)
        # self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # No experiments present yet
        self.assertIn(
            b"<em>There are no experiments in this project.</em>",
            response.content,
        )

        exp1 = Experiment(
            title="Latest1", description="the latest exp", created_by=self.user
        )
        exp1.save()
        acl = ExperimentACL(
            user=self.user,
            experiment=exp1,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        acl.save()
        self.project.experiments.add(exp1)
        self.experiments.append(exp1)

        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        response = project_latest_experiment(request, project_id=self.project.id)
        self.assertEqual(response.status_code, 200)
        # self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # Check for latest experiment
        self.assertIn(
            b"Latest1",
            response.content,
        )

        exp2 = Experiment(
            title="A new latest experiment",
            description="the new latest exp",
            created_by=self.user,
        )
        exp2.save()
        acl = ExperimentACL(
            user=self.user,
            experiment=exp2,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        acl.save()
        self.project.experiments.add(exp2)
        self.experiments.append(exp2)

        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        response = project_latest_experiment(request, project_id=self.project.id)
        self.assertEqual(response.status_code, 200)
        # self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # Check for the even newer experiment
        self.assertIn(
            b"A new latest experiment",
            response.content,
        )

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_recent_experiments(self, mock_webpack_get_bundle):
        from django.http import HttpRequest
        from tardis.apps.projects.ajax_pages import project_recent_experiments

        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        response = project_recent_experiments(request, project_id=self.project.id)
        self.assertEqual(response.status_code, 200)
        # self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # No experiments present yet
        self.assertEqual(
            b"\n",
            response.content,
        )

        exp1 = Experiment(
            title="Latest1", description="the latest exp", created_by=self.user
        )
        exp1.save()
        acl = ExperimentACL(
            user=self.user,
            experiment=exp1,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        acl.save()
        self.project.experiments.add(exp1)
        self.experiments.append(exp1)

        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        response = project_recent_experiments(request, project_id=self.project.id)
        self.assertEqual(response.status_code, 200)
        # self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # Check for latest experiment
        self.assertIn(
            b"Latest1",
            response.content,
        )

        exp2 = Experiment(
            title="A new latest experiment",
            description="the new latest exp",
            created_by=self.user,
        )
        exp2.save()
        acl = ExperimentACL(
            user=self.user,
            experiment=exp2,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        acl.save()
        self.project.experiments.add(exp2)
        self.experiments.append(exp2)

        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        response = project_recent_experiments(request, project_id=self.project.id)
        self.assertEqual(response.status_code, 200)
        # self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # Check for latest experiment
        self.assertIn(
            b"Latest1",
            response.content,
        )
        # Check for the even newer experiment
        self.assertIn(
            b"A new latest experiment",
            response.content,
        )

    # @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    # def test_project_metadata(self, mock_webpack_get_bundle):
    # Currently metadata isn't embedded on any page, so defer this test
    # until it is
    #    pass

    def tearDown(self):
        self.project.delete()
        self.user.delete()
        for exp in self.experiments:
            exp.delete()
