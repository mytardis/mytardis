# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2011, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""
tests.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor:: Ulrich Felzmann <ulrich.felzmann@versi.edu.au>
.. moduleauthor:: Gerson Galang <gerson.galang@versi.edu.au>

"""

import unittest

from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User

from ..models import Experiment, ExperimentACL, Dataset, DatasetACL


# http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
class UserInterfaceTestCase(TestCase):
    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_root(self, mock_webpack_get_bundle):
        self.assertEqual(Client().get("/").status_code, 200)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_urls(self, mock_webpack_get_bundle):
        c = Client()
        urls = [
            "/login/",
            "/about/",
            "/public_data/",
        ]

        for u in urls:
            response = c.get(u)
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def test_urls_with_some_content(self, mock_webpack_get_bundle):
        # Things that might tend to be in a real live system
        user = "testuser"
        pwd = User.objects.make_random_password()
        user = User.objects.create(
            username=user,
            email="testuser@example.test",
            first_name="Test",
            last_name="User",
        )
        user.set_password(pwd)
        user.save()
        experiment = Experiment.objects.create(
            title="Test Experiment",
            created_by=user,
            public_access=Experiment.PUBLIC_ACCESS_FULL,
        )
        experiment.save()
        acl = ExperimentACL(
            user=user,
            experiment=experiment,
            canRead=True,
            canDownload=True,
            canWrite=True,
            canDelete=True,
            canSensitive=True,
            isOwner=True,
        )
        acl.save()
        dataset = Dataset(description="test dataset")
        dataset.save()
        dataset.experiments.add(experiment)
        dataset.save()
        if not settings.ONLY_EXPERIMENT_ACLS:
            acl = DatasetACL(
                user=user,
                dataset=dataset,
                canRead=True,
                canDownload=True,
                canWrite=True,
                canDelete=True,
                canSensitive=True,
                isOwner=True,
            )
            acl.save()

        # Test everything works
        c = Client()
        c.login(username=user, password=pwd)
        urls = ["/about/"]
        urls += ["/mydata/"]
        urls += ["/experiment/view/%d/" % experiment.id]
        urls += [
            "/ajax/experiment/%d/%s" % (experiment.id, tabpane)
            for tabpane in ("description", "datasets", "rights")
        ]
        urls += ["/ajax/datafile_list/%d/" % dataset.id]
        urls += ["/ajax/dataset_metadata/%d/" % dataset.id]

        for u in urls:
            response = c.get(u)
            self.assertEqual(
                response.status_code,
                200,
                "%s should have returned 200 but returned %d"
                % (u, response.status_code),
            )
        # Test stat page is not available for non super_user
        response = c.get("/stats/")
        self.assertEqual(
            response.status_code,
            302,
            "%s should have returned 302 but returned %d"
            % ("/stats/", response.status_code),
        )
        # Test super_user can access stats page
        c.logout()
        user.is_superuser = True
        user.save()
        c.login(username=user, password=pwd)
        response = c.get("/stats/")
        self.assertEqual(
            response.status_code,
            200,
            "%s should have returned 200 but returned %d"
            % ("/stats/", response.status_code),
        )
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

    def test_login(self):
        from django.contrib.auth.models import User

        user = "user2"
        pwd = "test"
        email = ""
        User.objects.create_user(user, email, pwd)

        self.assertEqual(self.client.login(username=user, password=pwd), True)


def suite():
    userInterfaceSuite = unittest.TestLoader().loadTestsFromTestCase(
        UserInterfaceTestCase
    )

    allTests = unittest.TestSuite(
        [
            userInterfaceSuite,
        ]
    )
    return allTests
