# -*- coding: utf-8 -*-
#
# Copyright (c) 2011-2011, RMIT e-Research Office
#   (RMIT University, Australia)
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
tests.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Ian Thomas <Ian.Edward.Thomas@rmit.edu.au>

"""

from django.test import TestCase
from nose.plugins.skip import SkipTest        
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager
import logging
from tardis.tardis_portal import models

logger = logging.getLogger(__name__)

class MicroTagsTestCase(TestCase):

    def setUp(self):
        from django.contrib.auth.models import User
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

    def test_save_metadata(self):
        # Removed temporarily due to incorrect exiv2 version being imported by hudson
 	raise SkipTest()
        from os import path
        try:
            from tardis.apps.microtardis.filters.microtags import MicroTagsFilter
        except:
            raise SkipTest()

        filename = path.join(path.abspath(path.dirname(__file__)), 'testing/FEIQuanta200/test.tif')

        exp = models.Experiment(title='test exp1',
                                institution_name='rmit',
                                approved=True,
                                created_by=self.user,
                                public=False)
        exp.save()
        
        logger.debug("experiment %s" % exp)
        logger.debug("filename %s" % filename)
 
        dataset = models.Dataset(description="dataset description...",
                                 experiment=exp)
        dataset.save()
        df_file = models.Dataset_File(dataset=dataset,
                                      filename='test.tif',
                                      url=filename,
                                      protocol='staging')
        df_file.save()

        #self.assertEqual("",models.Schema.objects.all())
        sch = models.Schema.objects.get(name="FEIQuanta-2")
        self.assertEqual("FEIQuanta-2",sch.name)
        datafileparameterset = models.DatafileParameterSet.objects.get(
            schema=sch, dataset_file=df_file)
        psm = ParameterSetManager(parameterset=datafileparameterset)
        self.assertEqual(1,len(psm.parameters))
        self.assertEqual(str(psm.get_param("Brightness").numerical_value),"21.2")
                
        
        sch = models.Schema.objects.get(name="FEIQuanta-1")
        self.assertEqual("FEIQuanta-1",sch.name)
        datafileparameterset = models.DatafileParameterSet.objects.get(
            schema=sch, dataset_file=df_file)
        psm = ParameterSetManager(parameterset=datafileparameterset)
        self.assertEqual(2,len(psm.parameters))
        self.assertEqual(str(psm.get_param("HV").numerical_value),"25000.0")
                
        self.assertEqual(str(psm.get_param("Spot").numerical_value),"5.0")
                
