# -*- coding: utf-8 -*-
#
# Copyright (c) 2010, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010, VeRSI Consortium
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
test_tokens.py
"""
import re
import sys

import datetime
from datetime import datetime as old_datetime

from django.test import RequestFactory
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User

from ..models import Experiment
from ..models import ObjectACL
from ..models import Token

from ..views.authorisation import retrieve_access_list_tokens


class FrozenTime:
    def __init__(self, *args, **kwargs):
        self.year = args[0]
        self.month = args[1]
        self.day = args[2]
        self.hour = args[3]

    def __lt__(self, b):
        return old_datetime(self.year, self.month, self.day, self.hour) < \
            old_datetime(b.year, b.month, b.day, b.hour)

    @classmethod
    def freeze_time(cls, time):
        cls.frozen_time = time

    @classmethod
    def now(cls):
        return cls.frozen_time

    def __str__(self):
        return "%s %s %s  %s" % (self.year, self.month, self.day, self.hour)


def _raise_integrity_error():
    from django.db import IntegrityError
    raise IntegrityError()


class TokenTestCase(TestCase):

    urls = 'tardis.tardis_portal.tests.urls'

    def setUp(self):
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)
        self.experiment = Experiment(created_by=self.user)
        self.experiment.save()

        sys.modules['datetime'].datetime = FrozenTime

    def tearDown(self):
        sys.modules['datetime'].datetime = old_datetime

# expiry should default to today plus TOKEN_EXPIRY_DAYS
    def test_default_expiry(self):
        the_time = old_datetime(2011, 9, 20, 1, 52, 31, 570376)
        FrozenTime.freeze_time(the_time)
        expected_expiry = the_time.date() + \
            datetime.timedelta(settings.TOKEN_EXPIRY_DAYS)

        t = Token()

        self.assertEqual(expected_expiry, t.expiry_date)

# token is valid up to and including day of expiry
    def test_is_expired(self):
        now = old_datetime(2011, 8, 20, 0, 0, 0, 1)

        FrozenTime.freeze_time(now)

        today = now.date()

        yesterday = today - datetime.timedelta(1)
        tomorrow = today + datetime.timedelta(1)

        t = Token()
        t.expiry_date = yesterday

        self.assertTrue(t.is_expired())

        t.expiry_date = today
        self.assertFalse(t.is_expired())

        t.expiry_date = tomorrow
        self.assertFalse(t.is_expired())

    def test_get_session_expiry(self):
        three_am = old_datetime(2011, 8, 20, 3)
        now = three_am

        FrozenTime.freeze_time(now)
        tomorrow_4am = old_datetime(2011, 8, 21, 4)

        t = Token()
        expected_expiry = tomorrow_4am

        self.assertEqual(expected_expiry.year, t.get_session_expiry().year)
        self.assertEqual(expected_expiry.month, t.get_session_expiry().month)
        self.assertEqual(expected_expiry.day, t.get_session_expiry().day)
        self.assertEqual(expected_expiry.hour, t.get_session_expiry().hour)

    def test_get_session_expiry_near_expiry(self):
        now = old_datetime(2011,8,20,3)
        FrozenTime.freeze_time(now)

        t = Token()
        t.expiry_date = now.date()

        expected_expiry = old_datetime(2011, 8, 20, 23, 59, 59)

        actual_expiry = t.get_session_expiry()

        self.assertEqual(expected_expiry.year, actual_expiry.year)
        self.assertEqual(expected_expiry.month, actual_expiry.month)
        self.assertEqual(expected_expiry.day, actual_expiry.day)
        self.assertEqual(expected_expiry.hour, actual_expiry.hour)

    def test_get_session_expiry_expired_token(self):
        now = old_datetime(2011, 8, 20, 13)
        FrozenTime.freeze_time(now)

        yesterday = (now - datetime.timedelta(1)).date()

        t = Token()
        t.expiry_date = yesterday

        self.assertEqual(now.year, t.get_session_expiry().year)
        self.assertEqual(now.month, t.get_session_expiry().month)
        self.assertEqual(now.day, t.get_session_expiry().day)
        self.assertEqual(now.hour, t.get_session_expiry().hour)


# check that we don't loop indefinitely when success is impossible
# check no token is assigned
    def test_save_with_random_token_failures(self):
        from django.core.exceptions import ObjectDoesNotExist

        t = Token()
        self.assertRaises(ObjectDoesNotExist, t.save_with_random_token)
        self.assertEqual('', t.token)

        t = Token(user=self.user)
        self.assertRaises(ObjectDoesNotExist, t.save_with_random_token)
        self.assertEqual('', t.token)

        t = Token(experiment=self.experiment)
        self.assertRaises(ObjectDoesNotExist, t.save_with_random_token)
        self.assertEqual('', t.token)

# check that failure happens eventually
    def test_save_with_random_token_gives_up(self):
        from django.db import IntegrityError
        t = Token(user=self.user, experiment=self.experiment)

        t.save = _raise_integrity_error
        self.assertRaises(IntegrityError, t.save_with_random_token)

# should have tried to assign at least one token
        self.assertTrue(len(t.token) > 0)

    def test_save_with_random_token(self):
        t = Token(user=self.user, experiment=self.experiment)
        t.save_with_random_token()
        self.assertTrue(len(t.token) > 0)

    def test_retrieve_access_list_tokens(self):
        sys.modules['datetime'].datetime = old_datetime
        experiment = Experiment(title='test exp1', created_by=self.user)
        experiment.save()
        acl = ObjectACL(pluginId='django_user',
                        entityId=str(self.user.id),
                        content_object=experiment,
                        canRead=True,
                        canWrite=True,
                        canDelete=True,
                        isOwner=True)
        acl.save()

        now = old_datetime.now()
        today = now.date()
        tomorrow = today + datetime.timedelta(1)

        token = Token(experiment=experiment, user=self.user)
        token.expiry_date = tomorrow
        token.save()

        factory = RequestFactory()
        request = factory.get(
            '/experiment/control_panel/%s/access_list/tokens/'
            % experiment.id)
        request.user = self.user
        response = retrieve_access_list_tokens(
            request, experiment_id=experiment.id)
        matches = re.findall(
            'href="/token/delete/[0-9]+/"', response.content)
        self.assertEqual(len(matches), 1)
        self.assertIn(
            'href="/token/delete/%s/"' % token.id,
            response.content)
