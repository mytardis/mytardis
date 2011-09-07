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
from django.test import TestCase
from django.conf import settings

from tardis.tardis_portal.models import Token

import datetime
from datetime import datetime as old_datetime

import sys


class FrozenTime:
    def __init__(*args, **kwargs):
        pass

    @classmethod
    def freeze_time(cls, time):
        cls.frozen_time = time

    @classmethod
    def now(cls):
        return cls.frozen_time


def _raise_integrity_error():
    from django.db import IntegrityError
    raise IntegrityError()


class TokenTestCase(TestCase):

    urls = 'tardis.tardis_portal.tests.urls'

    def setUp(self):
        from django.contrib.auth.models import User
        from tardis.tardis_portal.models import Experiment
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
