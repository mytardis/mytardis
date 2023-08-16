"""
test_ajax.py

Tests for ajax view methods relating to projects

.. moduleauthor::  Mike Laverick <mike.laverick@auckland.ac.nz>

"""
from unittest import skipIf
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.http import HttpRequest

from django.test import TestCase

from tardis.apps.projects.ajax_pages import (
    project_recent_experiments,
    project_latest_experiment,
    retrieve_project_metadata,
)
from tardis.tardis_portal.models import Experiment, ExperimentACL, Schema, ParameterName
from ...models import (
    Project,
    Institution,
    ProjectACL,
    ProjectParameter,
    ProjectParameterSet,
)


@skipIf(settings.ONLY_EXPERIMENT_ACLS is True, "skipping Micro ACL specific test")
class AjaxTestCase(TestCase):
    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        # Create test owner
        username, email, password = ("testuser", "testuser@example.test", "password")
        user = User.objects.create_user(username, email, password)
        for perm in ("add_project", "change_project"):
            user.user_permissions.add(Permission.objects.get(codename=perm))
        user.save()
        # Data used in tests
        self.user, self.username, self.password = (user, username, password)

        # Create user with no perms on project
        username, email, password = (
            "testuser_1",
            "testuser@example.test_1",
            "password_1",
        )
        user = User.objects.create_user(username, email, password)
        for perm in ("add_project", "change_project"):
            user.user_permissions.add(Permission.objects.get(codename=perm))
        user.save()
        # Data used in tests
        self.user_1, self.username_1, self.password_1 = (user, username, password)
        self.userprofile_1 = self.user_1.userprofile

        self.institution = Institution.objects.create(name="University of Auckland")
        self.institution.save()

        self.project = Project(
            name="Test Project 1",
            description="This is a test.",
            principal_investigator=self.user,
            created_by=self.user,
        )
        self.project.save()
        # Explicit ACL creation for owner
        acl = ProjectACL(
            user=self.user,
            project=self.project,
            canRead=True,
            canSensitive=True,
            canWrite=True,
            isOwner=True,
            aclOwnershipType=ProjectACL.OWNER_OWNED,
        )
        acl.save()
        # ACL creation for read_only user
        acl = ProjectACL(
            user=self.user_1,
            project=self.project,
            canRead=True,
            aclOwnershipType=ProjectACL.OWNER_OWNED,
        )
        acl.save()

        self.project.institution.add(self.institution)

        # initialise empty list to make sure they are torn down later
        self.experiments = []

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_latest_experiment(self, mock_webpack_get_bundle):
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

        # Check for the even newer experiment
        self.assertIn(
            b"A new latest experiment",
            response.content,
        )

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_recent_experiments(self, mock_webpack_get_bundle):
        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        response = project_recent_experiments(request, project_id=self.project.id)
        self.assertEqual(response.status_code, 200)

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

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_project_metadata(self, mock_webpack_get_bundle):
        """
        Test that the project metadata template will function properly.
        Check that permissions are respected for adding/editing metadata,
        and viewing sensitive metadata.
        """

        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        response = retrieve_project_metadata(request, project_id=self.project.id)
        self.assertEqual(response.status_code, 200)

        # Check for no metadata in template
        self.assertIn(
            b"There is no metadata for this project",
            response.content,
        )
        # Check owner can see "Add Project Metadata"
        self.assertIn(
            b"Add Project Metadata",
            response.content,
        )

        request = HttpRequest()
        request.method = "GET"
        request.user = self.user_1
        response = retrieve_project_metadata(request, project_id=self.project.id)
        self.assertEqual(response.status_code, 200)

        # Check read_only user cannot see "Add Project Metadata"
        self.assertNotIn(
            b"Add Project Metadata",
            response.content,
        )

        # Create some metadata for viewing
        test_schema = Schema.objects.create(
            namespace="http://schema.namespace/project/1", type=Schema.PROJECT
        )
        test_schema.save()
        test_param_name = ParameterName.objects.create(
            schema=test_schema, name="param1_name", data_type=ParameterName.STRING
        )
        test_param_name.save()
        test_param_name_sens = ParameterName.objects.create(
            schema=test_schema,
            name="param_name_sens",
            data_type=ParameterName.STRING,
            sensitive=True,
        )
        test_param_name_sens.save()
        pset = ProjectParameterSet.objects.create(
            project=self.project, schema=test_schema
        )
        pset.save()
        proj_param = ProjectParameter.objects.create(
            parameterset=pset,
            name=test_param_name,
            string_value="value1",
        )
        proj_param.save()
        proj_param_sens = ProjectParameter.objects.create(
            parameterset=pset,
            name=test_param_name_sens,
            string_value="sensitive_data",
        )
        proj_param_sens.save()

        # redo the request to see updated data for Owner
        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        response = retrieve_project_metadata(request, project_id=self.project.id)
        self.assertEqual(response.status_code, 200)

        # Check for metadata in template
        self.assertIn(
            b"value1",
            response.content,
        )
        self.assertIn(
            b"sensitive_data",
            response.content,
        )
        # Check owner can see "Add Project Metadata"
        self.assertIn(
            b"Add Project Metadata",
            response.content,
        )
        # Check owner can see "Edit Project Metadata"
        self.assertIn(
            b'<i class="fa fa-pencil"></i>',
            response.content,
        )

        # redo the request to see updated data for read_only user
        request = HttpRequest()
        request.method = "GET"
        request.user = self.user_1
        response = retrieve_project_metadata(request, project_id=self.project.id)
        self.assertEqual(response.status_code, 200)

        # Check for metadata in template
        self.assertIn(
            b"value1",
            response.content,
        )
        self.assertNotIn(
            b"sensitive_data",
            response.content,
        )
        # Check owner can see "Add Project Metadata"
        self.assertNotIn(
            b"Add Project Metadata",
            response.content,
        )
        # Check owner can see "Edit Project Metadata"
        self.assertNotIn(
            b'<i class="fa fa-pencil"></i>',
            response.content,
        )

    def tearDown(self):
        self.project.delete()
        self.user.delete()
        for exp in self.experiments:
            exp.delete()
