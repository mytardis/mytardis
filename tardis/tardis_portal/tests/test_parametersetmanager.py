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
test_views.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>

"""
from django.test import TestCase
from tardis.tardis_portal import models
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager


class ParameterSetManagerTestCase(TestCase):

    def setUp(self):
        from django.contrib.auth.models import User
        from tempfile import mkdtemp

        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

        self.test_dir = mkdtemp()

        self.exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                created_by=self.user,
                                )
        self.exp.save()

        self.dataset = models.Dataset(description="dataset description...",
                                 experiment=self.exp)
        self.dataset.save()

        self.datafile = models.Dataset_File(dataset=self.dataset,\
            filename="testfile.txt", url="file://1/testfile.txt")

        self.datafile.save()

        self.schema = models.Schema(namespace="http://localhost/psmtest/df/",
            name="Parameter Set Manager", type=3)

        self.schema.save()

        self.parametername1 = models.ParameterName(
            schema=self.schema, name="parameter1",
            full_name="Parameter 1")

        self.parametername1.save()

        self.parametername2 = models.ParameterName(
            schema=self.schema, name="parameter2",
            full_name="Parameter 2",
            data_type=models.ParameterName.NUMERIC)

        self.parametername2.save()

        self.datafileparameterset = models.DatafileParameterSet(
            schema=self.schema, dataset_file=self.datafile)

        self.datafileparameterset.save()

        self.datafileparameter1 = models.DatafileParameter(
            parameterset=self.datafileparameterset,
            name=self.parametername1, string_value="test1")

        self.datafileparameter1.save()

        self.datafileparameter2 = models.DatafileParameter(
            parameterset=self.datafileparameterset,
            name=self.parametername2, numerical_value=2)

        self.datafileparameter2.save()

    def tearDown(self):

        self.exp.delete()
        self.user.delete()
        self.parametername1.delete()
        self.parametername2.delete()
        self.schema.delete()

    def test_existing_parameterset(self):

        psm = ParameterSetManager(parameterset=self.datafileparameterset)

        self.assertTrue(psm.get_schema().namespace\
            == "http://localhost/psmtest/df/")

        self.assertTrue(psm.get_param("parameter1").string_value == "test1")

        self.assertTrue(psm.get_param("parameter2", True) == 2)

    def test_new_parameterset(self):

        psm = ParameterSetManager(parentObject=self.datafile,\
            schema="http://localhost/psmtest/df2/")

        self.assertTrue(psm.get_schema().namespace\
            == "http://localhost/psmtest/df2/")

        psm.set_param("newparam1", "test3", "New Parameter 1")

        self.assertTrue(psm.get_param("newparam1").string_value\
            == "test3")

        self.assertTrue(psm.get_param("newparam1").name.full_name\
            == "New Parameter 1")

        psm.new_param("newparam1", "test4")

        self.assertTrue(len(psm.get_params("newparam1", True)) == 2)

        psm.set_param_list("newparam2", ("a", "b", "c", "d"))

        self.assertTrue(len(psm.get_params("newparam2")) == 4)

        psm.set_params_from_dict(
            {"newparam2": "test5", "newparam3": 3})

        self.assertTrue(psm.get_param("newparam2", True) == "test5")

        # the newparam3 gets created and '3' is set to a string_value
        # since once cannot assume that an initial numeric value
        # will imply continuing numeric type for this new param
        self.assertTrue(psm.get_param("newparam3").string_value == '3')

        psm.delete_params("newparam1")

        self.assertTrue(len(psm.get_params("newparam1", True)) == 0)
