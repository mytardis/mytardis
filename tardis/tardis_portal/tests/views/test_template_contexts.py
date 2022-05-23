"""
test_template_contexts.py

Tests for view methods supplying context data to templates

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
import sys

from unittest.mock import patch
from flexmock import flexmock

from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User

from ...models import ExperimentACL, Experiment, Dataset, DataFile, DatasetACL


class ViewTemplateContextsTest(TestCase):
    def setUp(self):
        """
        setting up essential objects, copied from tests above
        """

        user = "tardis_user1"
        pwd = "secret"  # nosec
        email = ""
        self.user = User.objects.create_user(user, email, pwd)
        self.exp = Experiment(
            title="test exp1", institution_name="monash", created_by=self.user
        )
        self.exp.save()
        self.acl = ExperimentACL(
            user=self.user,
            experiment=self.exp,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        self.acl.save()
        self.dataset = Dataset(description="dataset description...")
        self.dataset.save()
        self.dataset.experiments.add(self.exp)
        self.dataset.save()

        self.datafile = DataFile(
            dataset=self.dataset, size=42, filename="foo", md5sum="junk"
        )
        self.datafile.save()

    def tearDown(self):
        self.user.delete()
        self.exp.delete()
        self.dataset.delete()
        self.datafile.delete()

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_experiment_view(self, mock_webpack_get_bundle):
        """
        test some template context parameters for an experiment view
        """
        from ...views.pages import ExperimentView
        from django.http import HttpRequest

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
                ["tgz", "/download/experiment/1/tgz/"],
                ["tar", "/download/experiment/1/tar/"],
            ],
        }
        views_module.should_call("render_response_index").with_args(
            _AnyMatcher(),
            "tardis_portal/view_experiment.html",
            _ContextMatcher(context),
        )
        view_fn = ExperimentView.as_view()
        response = view_fn(request, experiment_id=self.exp.id)
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
                "protocol": [["tar", "/download/experiment/1/tar/"]],
            }
            views_module.should_call("render_response_index").with_args(
                _AnyMatcher(),
                "tardis_portal/view_experiment.html",
                _ContextMatcher(context),
            )
            view_fn = ExperimentView.as_view()
            response = view_fn(request, experiment_id=self.exp.id)
            self.assertEqual(response.status_code, 200)
        finally:
            if saved_setting is not None:
                setattr(settings, "USER_AGENT_SENSING", saved_setting)
            else:
                delattr(settings, "USER_AGENT_SENSING")

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_dataset_view(self, mock_webpack_get_bundle):
        """
        test some context parameters for a dataset view
        """
        from ...views.pages import DatasetView
        from django.http import HttpRequest

        views_module = flexmock(sys.modules["tardis.tardis_portal.views"])
        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        request.groups = []
        context = {"default_organization": "test", "default_format": "tar"}
        views_module.should_call("render_response_index").with_args(
            _AnyMatcher(), "tardis_portal/view_dataset.html", _ContextMatcher(context)
        )
        view_fn = DatasetView.as_view()
        response = view_fn(request, dataset_id=self.dataset.id)
        if settings.ONLY_EXPERIMENT_ACLS:
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)
        else:
            self.assertEqual(response.status_code, 403)
            self.set_acl = DatasetACL(
                user=self.user,
                dataset=self.dataset,
                isOwner=True,
                canRead=True,
                canDownload=True,
                aclOwnershipType=DatasetACL.OWNER_OWNED,
            )
            self.set_acl.save()
            response = view_fn(request, dataset_id=self.dataset.id)
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
            context = {"default_organization": "classic", "default_format": "tar"}
            views_module.should_call("render_response_index").with_args(
                _AnyMatcher(),
                "tardis_portal/view_dataset.html",
                _ContextMatcher(context),
            )
            view_fn = DatasetView.as_view()
            response = view_fn(request, dataset_id=self.dataset.id)
            self.assertEqual(response.status_code, 200)
        finally:
            if saved_setting is not None:
                setattr(settings, "USER_AGENT_SENSING", saved_setting)
            else:
                delattr(settings, "USER_AGENT_SENSING")


class ExperimentListsTest(TestCase):
    def setUp(self):
        """
        setting up essential objects, copied from tests above
        """

        self.username = "tardis_user1"
        self.password = "secret"
        email = ""
        self.user = User.objects.create_user(self.username, email, self.password)
        self.exps = []
        self.acls = []
        for exp_num in range(1, 301):
            exp = Experiment.objects.create(
                title="Experiment %s" % exp_num, created_by=self.user
            )
            self.exps.append(exp)
            is_owner = exp_num <= 100
            acl = ExperimentACL.objects.create(
                user=self.user,
                experiment=exp,
                canRead=True,
                isOwner=is_owner,
                aclOwnershipType=ExperimentACL.OWNER_OWNED,
            )
            self.acls.append(acl)

    def tearDown(self):
        self.user.delete()
        for exp in self.exps:
            exp.delete()
        for acl in self.acls:
            acl.delete()

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_mydata_view(self, mock_webpack_get_bundle):
        """
        Test My Data view
        """
        from django.http import QueryDict, HttpRequest
        from ...views.pages import my_data
        from ...views.ajax_pages import retrieve_owned_exps_list

        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        response = my_data(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)
        # jQuery hasn't populated the div yet:
        self.assertIn(
            b'<div id="myowned" class="mydata panel-group experiments"></div>',
            response.content,
        )

        # Owned experiments:
        self.assertEqual(settings.OWNED_EXPS_PER_PAGE, 20)
        self.assertEqual(len([acl for acl in self.acls if acl.isOwner]), 100)
        request.GET = QueryDict("")
        response = retrieve_owned_exps_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b'<ul class="pagination justify-content-center"', response.content
        )
        self.assertIn(b"Page 1 of 5", response.content)

        # Now let's reduce the number of owned experiments from
        # 100 to 10, so pagination isn't needed:
        deleted_count = 0
        for acl in list(self.acls):
            exp = acl.experiment
            if acl.isOwner and deleted_count < 90:
                self.exps.remove(exp)
                self.acls.remove(acl)
                exp.delete()
                acl.delete()
                deleted_count += 1
        request.GET = QueryDict("")
        response = retrieve_owned_exps_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'<ul class="pagination"', response.content)

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_shared_view(self, mock_webpack_get_bundle):
        """
        Test Shared view
        """
        from django.http import QueryDict, HttpRequest
        from ...views.pages import shared
        from ...views.ajax_pages import retrieve_shared_exps_list

        request = HttpRequest()
        request.method = "GET"
        request.user = self.user
        response = shared(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # jQuery hasn't populated the div yet:
        self.assertIn(
            b'<div id="myshared" class="mydata accordion experiments"></div>',
            response.content,
        )

        # Shared experiments:
        self.assertEqual(settings.SHARED_EXPS_PER_PAGE, 20)
        self.assertEqual(len([acl for acl in self.acls if not acl.isOwner]), 200)
        request.GET = QueryDict("")
        response = retrieve_shared_exps_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b'<ul class="pagination justify-content-center"', response.content
        )
        self.assertIn(b"Page 1 of 10", response.content)

        # Now let's reduce the number of shared experiments from
        # 200 to 10, so pagination isn't needed:
        deleted_count = 0
        for acl in list(self.acls):
            exp = acl.experiment
            if not acl.isOwner and deleted_count < 190:
                self.exps.remove(exp)
                self.acls.remove(acl)
                exp.delete()
                acl.delete()
                deleted_count += 1
        request.GET = QueryDict("")
        response = retrieve_shared_exps_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'<ul class="pagination"', response.content)


class _ContextMatcher(object):
    def __init__(self, template):
        self.template = template

    def __eq__(self, other):
        for (key, value) in self.template.items():
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
