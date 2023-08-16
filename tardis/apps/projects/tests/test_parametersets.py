"""
test_parametersets.py

.. moduleauthor::  Mike Laverick <mike.laverick@auckland.ac.nz>

"""
from unittest import skipIf

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.test import RequestFactory, TestCase
from django.utils import timezone

from tardis.tardis_portal.models.parameters import ParameterName, Schema
from ..models import Project, ProjectACL, ProjectParameter, ProjectParameterSet
from ..views import add_project_par, edit_project_par


@skipIf(settings.ONLY_EXPERIMENT_ACLS is True, "skipping Micro ACL specific test")
class EditParameterSetTestCase(TestCase):
    def setUp(self):
        username = "tardis_user1"
        pwd = "secret"  # nosec
        email = ""
        self.user = User.objects.create_user(username, email, pwd)
        self.user.user_permissions.add(
            Permission.objects.get(codename="change_project")
        )
        self.user2 = User.objects.create_user("no_sensitive", "no@sens.com", "access")
        self.user2.user_permissions.add(
            Permission.objects.get(codename="change_project")
        )
        self.schema = Schema(
            namespace="http://localhost/psmtest/proj/",
            name="Parameter Set Manager",
            type=Schema.PROJECT,
        )
        self.schema.save()

        self.parametername1 = ParameterName(
            schema=self.schema,
            name="parameter1",
            full_name="Parameter 1",
            units="units1",
        )
        self.parametername1.save()

        self.parametername2 = ParameterName(
            schema=self.schema,
            name="parameter2",
            full_name="Parameter 2",
            data_type=ParameterName.NUMERIC,
            units="items",
        )
        self.parametername2.save()

        self.parametername3 = ParameterName(
            schema=self.schema,
            name="parameter3",
            full_name="Parameter 3",
            data_type=ParameterName.DATETIME,
        )
        self.parametername3.save()

        self.parametername_sens = ParameterName(
            schema=self.schema,
            name="parameter_sens",
            full_name="Parameter Sensitive",
            sensitive=True,
        )
        self.parametername_sens.save()

        self.project = Project(
            name="test proj1", created_by=self.user, principal_investigator=self.user
        )
        self.project.save()

        self.acl = ProjectACL(
            user=self.user,
            project=self.project,
            canRead=True,
            canSensitive=True,
            isOwner=True,
            aclOwnershipType=ProjectACL.OWNER_OWNED,
        )
        self.acl.save()

        self.acl2 = ProjectACL(
            user=self.user2,
            project=self.project,
            canRead=True,
            canWrite=True,  # Write but no Sensitive
            aclOwnershipType=ProjectACL.OWNER_OWNED,
        )
        self.acl2.save()

        self.projectparameterset = ProjectParameterSet(
            schema=self.schema, project=self.project
        )
        self.projectparameterset.save()

        self.proj_param1 = ProjectParameter.objects.create(
            parameterset=self.projectparameterset,
            name=self.parametername1,
            string_value="value1",
        )

        self.proj_param2 = ProjectParameter.objects.create(
            parameterset=self.projectparameterset,
            name=self.parametername2,
            numerical_value=987,
        )

        self.proj_param3 = ProjectParameter.objects.create(
            parameterset=self.projectparameterset,
            name=self.parametername3,
            datetime_value=timezone.now(),
        )

        self.proj_param_sens = ProjectParameter.objects.create(
            parameterset=self.projectparameterset,
            name=self.parametername_sens,
            string_value="sensitive info",
        )

    def test_edit_project_params(self):
        factory = RequestFactory()

        request = factory.get(
            "/ajax/edit_project_parameters/%s/" % self.projectparameterset.id
        )
        request.user = self.user
        response = edit_project_par(request, self.projectparameterset.id)
        self.assertEqual(response.status_code, 200)

        request = factory.post(
            "/ajax/edit_project_parameters/%s/" % self.projectparameterset.id,
            data={
                "csrfmiddlewaretoken": "bogus",
                "parameter1__1": "parameter1 value",
                "parameter2__2": 123,
                "parameter_sens__3": "new sensitive info",
            },
        )
        # Check that parameters were actually updated
        request.user = self.user
        response = edit_project_par(request, self.projectparameterset.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            ProjectParameter.objects.get(id=self.proj_param1.id).string_value,
            "parameter1 value",
        )
        self.assertEqual(
            ProjectParameter.objects.get(id=self.proj_param2.id).numerical_value, 123
        )
        self.assertEqual(
            ProjectParameter.objects.get(id=self.proj_param_sens.id).string_value,
            "new sensitive info",
        )

        request = factory.post(
            "/ajax/edit_project_parameters/%s/" % self.projectparameterset.id,
            data={
                "csrfmiddlewaretoken": "bogus",
                "parameter1__1": "parameter1",
                "parameter2__2": 1234,
                "parameter_sens__3": "Forbidden update",
            },
        )
        # Check that parameters 1, 2, were actually updated but not the sensitive one
        request.user = self.user2
        response = edit_project_par(request, self.projectparameterset.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            ProjectParameter.objects.get(id=self.proj_param1.id).string_value,
            "parameter1",
        )
        self.assertEqual(
            ProjectParameter.objects.get(id=self.proj_param2.id).numerical_value, 1234
        )
        self.assertEqual(
            ProjectParameter.objects.get(id=self.proj_param_sens.id).string_value,
            "new sensitive info",
        )

    def test_add_project_params(self):
        factory = RequestFactory()

        request = factory.get("/ajax/add_project_parameters/%s/" % self.project.id)
        request.user = self.user
        response = add_project_par(request, self.project.id)
        self.assertEqual(response.status_code, 200)

        request = factory.get(
            "/ajax/add_project_parameters/%s/?schema_id=%s"
            % (self.project.id, self.schema.id)
        )
        request.user = self.user
        response = add_project_par(request, self.project.id)
        self.assertEqual(response.status_code, 200)

        request = factory.post(
            "/ajax/add_project_parameters/%s/?schema_id=%s"
            % (self.project.id, self.schema.id),
            data={"csrfmiddlewaretoken": "bogus"},
        )
        request.user = self.user
        response = add_project_par(request, self.project.id)
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        self.project.delete()
        self.user.delete()
        self.user2.delete()
        self.schema.delete()
