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

from django.test import TestCase
from django.test.client import Client


class EquipmentTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def testSearchEquipmentForm(self):
        response = self.client.get('/equipment/search/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'] is not None)

    def testSearchEquipmentResult(self):
        response = self.client.post('/equipment/search/', {'key': 'PIL', })
        self.assertEqual(len(response.context['object_list']), 2)

    def testEquipmentDetail(self):
        response = self.client.get('/equipment/1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'].make, 'Dectris')
        self.assertEqual(response.context['object'].type, 'X-ray detector')

    def testEquipmentList(self):
        response = self.client.get('/equipment/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)


def suite():

    equipmentSuite = \
        unittest.TestLoader().loadTestsFromTestCase(EquipmentTestCase)

    allTests = unittest.TestSuite([equipmentSuite])
    return allTests
