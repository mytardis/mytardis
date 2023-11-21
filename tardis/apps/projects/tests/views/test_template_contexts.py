"""
test_template_contexts.py

Tests for view methods supplying context data to templates

.. moduleauthor::  Mike Laverick <mike.laverick@auckland.ac.nz>

"""
import sys
from unittest.mock import patch
from unittest import skipIf

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from flexmock import flexmock

# from ...models import DataFile, Dataset, DatasetACL, Experiment, ExperimentACL
from ...models import Project, ProjectACL


class _ContextMatcher(object):
    def __init__(self, template):
        self.template = template

    def __eq__(self, other):
        for key, value in self.template.items():
            if key not in other or other[key] != value:
                return False
        return True


class _AnyMatcher(object):
    def __eq__(self, other):
        return True


class _MiniMock(object):
    def __new__(cls, **attrs):
        result = object.__new__(cls)
        result.__dict__ = attrs
        return result


@skipIf(settings.ONLY_EXPERIMENT_ACLS is True, "skipping Micro ACL specific test")
class ViewTemplateContextsTest(TestCase):
    def setUp(self):
        """
        setting up essential objects, copied from tests above
        """

        user = "tardis_user1"
        pwd = "secret"  # nosec
        email = ""
        self.user = User.objects.create_user(user, email, pwd)
        self.proj = Project(
            name="test proj1", created_by=self.user, principal_investigator=self.user
        )
        self.proj.save()
        self.acl = ProjectACL(
            user=self.user,
            project=self.proj,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ProjectACL.OWNER_OWNED,
        )
        self.acl.save()

    def tearDown(self):
        self.user.delete()
        self.proj.delete()

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_project_view(self, mock_webpack_get_bundle):
        """
        test some template context parameters for an project view
        """
        from django.http import HttpRequest

        from ...views import ProjectView

        # Default behavior
        views_module = flexmock(sys.modules["tardis.tardis_portal.views"])
        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        request.groups = []
        context = {
            "organization": ["test", "test2"],
            "default_organization": "test",
            "default_format": "tar",
            "protocol": [
                ["tgz", "/download/project/1/tgz/"],
                ["tar", "/download/project/1/tar/"],
            ],
        }
        views_module.should_call("render_response_index").with_args(
            _AnyMatcher(),
            "tardis_portal/view_project.html",
            _ContextMatcher(context),
        )
        view_fn = ProjectView.as_view()
        response = view_fn(request, project_id=self.proj.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # Behavior with USER_AGENT_SENSING enabled and a request.user_agent
        saved_setting = getattr(settings, "USER_AGENT_SENSING", None)
        try:
            setattr(settings, "USER_AGENT_SENSING", True)
            request = HttpRequest()
            request.method = "GET"
            request.user = self.user
            request.groups = []
            mock_agent = _MiniMock(os=_MiniMock(family="Macintosh"))
            setattr(request, "user_agent", mock_agent)
            context = {
                "organization": ["classic", "test", "test2"],
                "default_organization": "classic",
                "default_format": "tar",
                "protocol": [["tar", "/download/project/1/tar/"]],
            }
            views_module.should_call("render_response_index").with_args(
                _AnyMatcher(),
                "tardis_portal/view_project.html",
                _ContextMatcher(context),
            )
            view_fn = ProjectView.as_view()
            response = view_fn(request, project_id=self.proj.id)
            self.assertEqual(response.status_code, 200)
        finally:
            if saved_setting is not None:
                setattr(settings, "USER_AGENT_SENSING", saved_setting)
            else:
                delattr(settings, "USER_AGENT_SENSING")


@skipIf(settings.ONLY_EXPERIMENT_ACLS is True, "skipping Micro ACL specific test")
class ProjectListsTest(TestCase):
    def setUp(self):
        """
        setting up essential objects, copied from tests above
        """

        self.creator_username = "tardis_creator1"
        self.creator_password = "creator_secret"
        creator_email = "test@test.com"
        self.creator_user = User.objects.create_user(
            self.creator_username, creator_email, self.creator_password
        )

        self.username = "tardis_user1"
        self.password = "secret"
        email = ""
        self.user = User.objects.create_user(self.username, email, self.password)
        self.projs = []
        self.acls = []
        for proj_num in range(1, 301):
            proj = Project.objects.create(
                name=f"Project {proj_num}s",
                created_by=self.creator_user,
                principal_investigator=self.creator_user,
            )
            self.projs.append(proj)
            # Projects don't distinguish between shared or owned, so this
            # is tweaked to ONLY give acls if "proj_num <= 100"
            if proj_num <= 100:
                acl = ProjectACL.objects.create(
                    user=self.user,
                    project=proj,
                    canRead=True,
                    isOwner=True,
                    aclOwnershipType=ProjectACL.OWNER_OWNED,
                )
                self.acls.append(acl)

    def tearDown(self):
        self.user.delete()
        self.creator_user.delete()
        for proj in self.projs:
            proj.delete()
        # for acl in self.acls:
        #    acl.delete()

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_mydata_view(self, mock_webpack_get_bundle):
        """
        Test My Data view
        """
        from django.http import HttpRequest, QueryDict

        from ...views import retrieve_owned_proj_list, my_projects

        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        response = my_projects(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)
        # jQuery hasn't populated the div yet:
        self.assertIn(
            b'<div id="myprojects" class="myprojectdata panel-group projects"></div>',
            response.content,
        )

        # Owned projects:
        self.assertEqual(settings.OWNED_EXPS_PER_PAGE, 20)
        self.assertEqual(len([acl for acl in self.acls if acl.isOwner]), 100)
        request.GET = QueryDict("")
        response = retrieve_owned_proj_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b'<ul class="pagination justify-content-center"', response.content
        )
        self.assertIn(b"Page 1 of 5", response.content)

        # Now let's reduce the number of owned projects from
        # 100 to 10, so pagination isn't needed:
        deleted_count = 0
        for acl in list(self.acls):
            proj = acl.project
            if acl.isOwner and deleted_count < 90:
                self.projs.remove(proj)
                self.acls.remove(acl)
                proj.delete()
                # acl.delete()
                deleted_count += 1
        request.GET = QueryDict("")
        response = retrieve_owned_proj_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'<ul class="pagination"', response.content)
