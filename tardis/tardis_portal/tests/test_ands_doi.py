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
test_ands_doi.py
"""
from django.conf import settings
from django.test import TestCase

from tardis.tardis_portal.ands_doi import DOIService
from tardis.tardis_portal.models import User, Experiment, Schema, ParameterName


class ANDSDOITestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('test', '', 'test')
        self.expt = Experiment(title='test exp1',
                                institution_name='monash',
                                created_by=self.user,
                                )
        self.schema, _ = Schema.objects.get_or_create(namespace=settings.DOI_NAMESPACE)
        self.doi_name, _ = ParameterName.objects.get_or_create(schema=self.schema, full_name='DOI', name='doi')
        self.expt.save()
        settings.DOI_ENABLE = True

    def tearDown(self):
        settings.DOI_ENABLE = False

    def test_init(self):
        doi_service = DOIService(self.expt)

    def test_get_doi_none(self):
        doi_service = DOIService(self.expt)
        self.assertEquals(None, doi_service.get_doi())
