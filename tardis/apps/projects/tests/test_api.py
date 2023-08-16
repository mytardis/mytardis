"""
Testing the Project-related resources in the App's Tastypie-based REST API
.. moduleauthor:: Mike Laverick <mike.laverick@auckland.ac.nz>
"""
import json
from unittest import skipIf

from django.conf import settings
from django.contrib.auth.models import Permission, User
from tastypie.test import ResourceTestCaseMixin

from tardis.tardis_portal.models.access_control import ExperimentACL
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.parameters import (
    ParameterName,
    Schema,
)
from ..models import (
    Institution,
    Project,
    ProjectACL,
    ProjectParameter,
    ProjectParameterSet,
)


from . import ModelTestCase


@skipIf(settings.ONLY_EXPERIMENT_ACLS is True, "skipping Micro ACL specific test")
class ProjectResourceTest(ResourceTestCaseMixin, ModelTestCase):
    def setUp(self):
        super().setUp()
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

        # create a schema and two parameternames for later
        schema_name = "http://proji-mental.com/"
        self.test_schema = Schema(namespace=schema_name, type=Schema.PROJECT)
        self.test_schema.save()
        self.test_parname1 = ParameterName(
            schema=self.test_schema,
            name="projparameter1",
            data_type=ParameterName.STRING,
        )
        self.test_parname1.save()
        self.test_parname2 = ParameterName(
            schema=self.test_schema,
            name="projparameter2",
            data_type=ParameterName.NUMERIC,
        )
        self.test_parname2.save()

    def get_credentials(self):
        return self.create_basic(username=self.username, password=self.password)

    def test_post_project(self):
        schema_id = Schema.objects.first().id
        parm_id = ParameterName.objects.first().id
        post_data = {
            "name": "Test Project",
            "description": "test description",
            "institution": ["/api/v1/institution/%d/" % self.institution.id],
            "principal_investigator": self.username,
            "parameter_sets": [
                {
                    "schema": "http://proji-mental.com/",
                    "parameters": [
                        {
                            "name": "/api/v1/parametername/%d/" % parm_id,
                            "string_value": "Test16",
                        },
                        {
                            "name": "/api/v1/parametername/%d/" % (parm_id + 1),
                            "numerical_value": "244",
                        },
                    ],
                },
                {
                    "schema": "/api/v1/schema/%d/" % schema_id,
                    "parameters": [
                        {"name": "projparameter1", "string_value": "Test16"},
                        {"name": "projparameter2", "value": "51244"},
                    ],
                },
            ],
        }
        project_count = Project.objects.count()
        parameterset_count = ProjectParameterSet.objects.count()
        parameter_count = ProjectParameter.objects.count()
        self.assertHttpCreated(
            self.api_client.post(
                "/api/v1/project/",
                data=post_data,
                authentication=self.get_credentials(),
            )
        )
        self.assertEqual(project_count + 1, Project.objects.count())
        self.assertEqual(parameterset_count + 2, ProjectParameterSet.objects.count())
        self.assertEqual(parameter_count + 4, ProjectParameter.objects.count())

        # Now lets repeat the test but also bundle in some experiment URIs,
        # and also users and groups access

        # create some experiments that the user has write access to
        exp1 = Experiment(
            title="Experiment 1", description="test experiment 1", created_by=self.user
        )
        exp1.save()
        acl = ExperimentACL(
            user=self.user,
            experiment=exp1,
            canRead=True,
            canWrite=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        acl.save()
        exp2 = Experiment(
            title="Experiment 2", description="test experiment 2", created_by=self.user
        )
        exp2.save()
        acl = ExperimentACL(
            user=self.user,
            experiment=exp2,
            canRead=True,
            canWrite=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        acl.save()

        post_data = {
            "name": "Test Project 2",
            "description": "test description",
            "institution": ["/api/v1/institution/%d/" % self.institution.id],
            "principal_investigator": self.username,
            "parameter_sets": [
                {
                    "schema": "http://proji-mental.com/",
                    "parameters": [
                        {
                            "name": "/api/v1/parametername/%d/" % parm_id,
                            "string_value": "Test16",
                        },
                        {
                            "name": "/api/v1/parametername/%d/" % (parm_id + 1),
                            "numerical_value": "244",
                        },
                    ],
                },
                {
                    "schema": "/api/v1/schema/%d/" % schema_id,
                    "parameters": [
                        {"name": "projparameter1", "string_value": "Test16"},
                        {"name": "projparameter2", "value": "51244"},
                    ],
                },
            ],
            "users": [
                (self.username_1, False, False, False),
                # ("dummy_user", True, True, True), Enabling this requires LDAP to be mocked
            ],
            "groups": [("dummy_group", False, False, False)],
            "experiments": [
                "/api/v1/experiment/%d/" % exp1.id,
                "/api/v1/experiment/%d/" % exp2.id,
            ],
        }

        project_count = Project.objects.count()
        parameterset_count = ProjectParameterSet.objects.count()
        parameter_count = ProjectParameter.objects.count()
        self.assertHttpCreated(
            self.api_client.post(
                "/api/v1/project/",
                data=post_data,
                authentication=self.get_credentials(),
            )
        )
        self.assertEqual(project_count + 1, Project.objects.count())
        self.assertEqual(parameterset_count + 2, ProjectParameterSet.objects.count())
        self.assertEqual(parameter_count + 4, ProjectParameter.objects.count())

    def test_get_project_experiments(self):
        # Create Project to test
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

        # test result with no experiments
        response = self.api_client.get(
            "/api/v1/project/%d/project-experiments/" % self.project.id,
            authentication=self.get_credentials(),
        )
        self.assertHttpOK(response)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data["objects"]), 0)
        # now test with 2 experiments
        # create some experiments that the user has write access to
        exp1 = Experiment(
            title="Experiment 1", description="test experiment 1", created_by=self.user
        )
        exp1.save()
        acl = ExperimentACL(
            user=self.user,
            experiment=exp1,
            canRead=True,
            canWrite=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        acl.save()
        exp2 = Experiment(
            title="Experiment 2", description="test experiment 2", created_by=self.user
        )
        exp2.save()
        self.project.experiments.add(exp1)
        acl = ExperimentACL(
            user=self.user,
            experiment=exp2,
            canRead=True,
            canWrite=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        acl.save()
        self.project.experiments.add(exp2)

        # test result with no experiments
        response = self.api_client.get(
            "/api/v1/project/%d/project-experiments/" % self.project.id,
            authentication=self.get_credentials(),
        )
        self.assertHttpOK(response)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data["objects"]), 2)


@skipIf(settings.ONLY_EXPERIMENT_ACLS is True, "skipping Micro ACL specific test")
class ProjectAPIAuthTest(ResourceTestCaseMixin, ModelTestCase):
    def setUp(self):
        super().setUp()
        # Create test owner
        username, email, password = ("testuser", "testuser@example.test", "password")
        user = User.objects.create_user(username, email, password)
        for perm in ("add_project", "change_project"):
            user.user_permissions.add(Permission.objects.get(codename=perm))
        user.save()
        # Data used in tests
        self.user, self.username, self.password = (user, username, password)

        # Create user with no global perms on project
        username, email, password = (
            "testuser_1",
            "testuser@example.test_1",
            "password_1",
        )
        user = User.objects.create_user(username, email, password)
        user.save()
        # Data used in tests
        self.user_1, self.username_1, self.password_1 = (user, username, password)
        self.userprofile_1 = self.user_1.userprofile

        # Create user with no individual perms on project
        username, email, password = (
            "testuser_2",
            "testuser@example.test_2",
            "password_2",
        )
        user = User.objects.create_user(username, email, password)
        user.save()
        # Data used in tests
        self.user_2, self.username_2, self.password_2 = (user, username, password)
        self.userprofile_2 = self.user_2.userprofile

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

        self.project2 = Project(
            name="Test Project 2",
            description="This is a test as well.",
            principal_investigator=self.user,
            created_by=self.user,
        )
        self.project2.save()
        # Explicit ACL creation for owner
        acl = ProjectACL(
            user=self.user,
            project=self.project2,
            canRead=True,
            canSensitive=True,
            canWrite=True,
            isOwner=True,
            aclOwnershipType=ProjectACL.OWNER_OWNED,
        )
        acl.save()

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

    def get_credentials(self):
        return self.create_basic(username=self.username, password=self.password)

    def get_credentials_bad(self):
        return self.create_basic(username=self.username_1, password=self.password_1)

    def get_credentials_noacl(self):
        return self.create_basic(username=self.username_2, password=self.password_2)

    def test_read_list_project(self):
        # test project list for good user
        response = self.api_client.get(
            "/api/v1/project/",
            authentication=self.get_credentials(),
        )
        self.assertHttpOK(response)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data["objects"]), 2)

        # test project list for bad user
        response = self.api_client.get(
            "/api/v1/project/",
            authentication=self.get_credentials_bad(),
        )
        # should go through but be empty
        self.assertHttpOK(response)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data["objects"]), 0)

        # test project list for noacl user
        response = self.api_client.get(
            "/api/v1/project/",
            authentication=self.get_credentials_bad(),
        )
        # should go through but be empty
        self.assertHttpOK(response)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data["objects"]), 0)

    def test_read_list_projectparameterset(self):
        # test project list for good user
        response = self.api_client.get(
            "/api/v1/projectparameterset/",
            authentication=self.get_credentials(),
        )
        self.assertHttpOK(response)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data["objects"]), 1)

        # test project list for bad user
        response = self.api_client.get(
            "/api/v1/projectparameterset/",
            authentication=self.get_credentials_bad(),
        )
        # should go through but be empty
        self.assertHttpOK(response)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data["objects"]), 0)

        # test project list for noacl user
        response = self.api_client.get(
            "/api/v1/projectparameterset/",
            authentication=self.get_credentials_bad(),
        )
        # should go through but be empty
        self.assertHttpOK(response)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data["objects"]), 0)

    def test_read_list_projectparameter(self):
        # test project list for good user
        response = self.api_client.get(
            "/api/v1/projectparameter/",
            authentication=self.get_credentials(),
        )
        self.assertHttpOK(response)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data["objects"]), 2)

        # test project list for bad user
        response = self.api_client.get(
            "/api/v1/projectparameter/",
            authentication=self.get_credentials_bad(),
        )
        # should go through but be empty
        self.assertHttpOK(response)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data["objects"]), 0)

        # test project list for noacl user
        response = self.api_client.get(
            "/api/v1/projectparameter/",
            authentication=self.get_credentials_bad(),
        )
        # should go through but be empty
        self.assertHttpOK(response)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data["objects"]), 0)

    def test_read_list_projectacl(self):
        pass

    def test_read_list_institution(self):
        pass

    def test_read_detail_project(self):
        pass

    def test_read_detail_projectparameterset(self):
        pass

    def test_read_detail_projectparameter(self):
        pass

    def test_read_detail_projectacl(self):
        pass

    def test_read_detail_institution(self):
        pass
