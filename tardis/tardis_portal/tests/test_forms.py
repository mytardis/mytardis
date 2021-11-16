#!/usr/bin/env python
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
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE7
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
test_models.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>

"""
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from ..forms import RightsForm
from ..models import Experiment, License


class RightsFormTestCase(TestCase):

    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username='PUBLIC_USER_TEST')
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        self.restrictiveLicense = License(name="Restrictive License",
                                          url="http://example.test/rl",
                                          internal_description="Description...",
                                          allows_distribution=False)
        self.restrictiveLicense.save()
        self.permissiveLicense  = License(name="Permissive License",
                                          url="http://example.test/pl",
                                          internal_description="Description...",
                                          allows_distribution=True)
        self.permissiveLicense.save()
        self.inactiveLicense  = License(name="Inactive License",
                                          url="http://example.test/ial",
                                          internal_description="Description...",
                                          allows_distribution=True,
                                          is_active=False)
        self.inactiveLicense.save()

    def test_ensures_suitable_license(self):
        suitableCombinations = (
            (Experiment.PUBLIC_ACCESS_NONE, ''),
            (Experiment.PUBLIC_ACCESS_METADATA, ''),
            (Experiment.PUBLIC_ACCESS_NONE, self.restrictiveLicense.id),
            (Experiment.PUBLIC_ACCESS_METADATA, self.restrictiveLicense.id),
            (Experiment.PUBLIC_ACCESS_FULL, self.permissiveLicense.id),
        )
        unsuitableCombinations = (
            (Experiment.PUBLIC_ACCESS_NONE, self.permissiveLicense.id),
            (Experiment.PUBLIC_ACCESS_METADATA, self.permissiveLicense.id),
            (Experiment.PUBLIC_ACCESS_METADATA, self.inactiveLicense.id),
            (Experiment.PUBLIC_ACCESS_FULL, self.inactiveLicense.id),
            (Experiment.PUBLIC_ACCESS_FULL, ''),
            (Experiment.PUBLIC_ACCESS_FULL, self.restrictiveLicense.id),
        )

        # Check we accept valid input
        for public_access, license_id in suitableCombinations:
            data = {'public_access': str(public_access),
                    'license': license_id,
                    'legal_text': str('No legal Text')}
            form = RightsForm(data)
            self.assertTrue(form.is_valid(), form.errors)

        # Check we reject invalid input
        for public_access, license_id in unsuitableCombinations:
            data = {'public_access': str(public_access),
                    'license': license_id }
            form = RightsForm(data)
            self.assertFalse(form.is_valid())
