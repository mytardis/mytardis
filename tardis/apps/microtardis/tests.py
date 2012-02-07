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
.. moduleauthor::  Joanna H. Huang <Joanna.Huang@versi.edu.au>

"""

from django.test import TestCase
from django.conf import settings
from nose.plugins.skip import SkipTest        
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager
import logging
from tardis.tardis_portal import models

logger = logging.getLogger(__name__)

class EXIFTagsTestCase(TestCase):

  
    def tearDown(self):
        from shutil import rmtree
        rmtree(self.experiment_path)
          
    def setUp(self):
        from django.contrib.auth.models import User
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

    def test_save_metadata(self):
        from os import path
        try:
            from tardis.apps.microtardis.filters.exiftags import EXIFTagsFilter
        except:
            raise SkipTest()

        exp = models.Experiment(title='exp: test exif filter',
                                institution_name='rmit',
                                approved=True,
                                created_by=self.user,
                                public=False)
        exp.save()
        logger.debug("experiment %s" % exp)
        
        self.assertEqual(exp.get_or_create_directory(),
                         path.join(settings.FILE_STORE_PATH, str(exp.id)))

        self.experiment_path = path.join(settings.FILE_STORE_PATH, str(exp.id))
      
        
        dataset = models.Dataset(description="dataset description...", experiment=exp)
        dataset.save()
        
        ## FEIQuanta200 TIF image testing ##
        filename = path.join(path.abspath(path.dirname(__file__)), 'testing/Quanta200/test.tif')
        logger.debug("filename %s" % filename)
 
        df_file = models.Dataset_File(dataset=dataset, filename='test.tif', url=filename, protocol='staging')
        df_file.save()

        #self.assertEqual("",models.Schema.objects.all())
        sch = models.Schema.objects.get(name="Quanta200_EXIF")
        self.assertEqual("Quanta200_EXIF",sch.name)
        datafileparameterset = models.DatafileParameterSet.objects.get(schema=sch, dataset_file=df_file)
        psm = ParameterSetManager(parameterset=datafileparameterset)
        self.assertEqual(14,len(psm.parameters))
        self.assertEqual(str(psm.get_param("[User] UserText").string_value), "R-2")
        self.assertEqual(str(psm.get_param("[User] Date").string_value), "11/09/2010")
        self.assertEqual(str(psm.get_param("[User] Time").string_value), "03:28PM")
        self.assertEqual(str(psm.get_param("[Beam] HV").numerical_value), "25.0")
        self.assertEqual(str(psm.get_param("[Beam] Spot").numerical_value), "5.0")
        self.assertEqual(str(psm.get_param("[Scan] HorFieldSize").numerical_value), "2.13333e-05")
        self.assertEqual(str(psm.get_param("[Stage] WorkingDistance").numerical_value), "5.2")
        self.assertEqual(str(psm.get_param("[Vacuum] UserMode").string_value), "Lowvacuum")
        self.assertEqual(str(psm.get_param("[Vacuum] CHPressure").string_value), "0.9976 Torr (1.33 mbar)")
        self.assertEqual(str(psm.get_param("[Detectors] Name").string_value), "Lfd")
        self.assertEqual(str(psm.get_param("[Lfd] Contrast").numerical_value), "88.2")
        self.assertEqual(str(psm.get_param("[Lfd] Brightness").numerical_value), "21.2")
        
        ## nanoSEM TIF image testing ##
        filename = path.join(path.abspath(path.dirname(__file__)), 'testing/NovaNanoSEM/test.tif')
        logger.debug("filename %s" % filename)
 
        df_file = models.Dataset_File(dataset=dataset, filename='test.tif', url=filename, protocol='staging')
        df_file.save()

        #self.assertEqual("",models.Schema.objects.all())
        sch = models.Schema.objects.get(name="NovaNanoSEM_EXIF")
        self.assertEqual("NovaNanoSEM_EXIF",sch.name)
        datafileparameterset = models.DatafileParameterSet.objects.get(schema=sch, dataset_file=df_file)
        psm = ParameterSetManager(parameterset=datafileparameterset)
        self.assertEqual(14,len(psm.parameters))
        self.assertEqual(str(psm.get_param("[User] UserText").string_value), "")
        self.assertEqual(str(psm.get_param("[User] Date").string_value), "03/29/2011")
        self.assertEqual(str(psm.get_param("[User] Time").string_value), "10:10:52 AM")
        self.assertEqual(str(psm.get_param("[Beam] HV").numerical_value), "15.0")
        self.assertEqual(str(psm.get_param("[Beam] Spot").numerical_value), "3.5")
        self.assertEqual(str(psm.get_param("[Scan] HorFieldSize").numerical_value), "0.00018592")
        self.assertEqual(str(psm.get_param("[Stage] WorkingDistance").numerical_value), "4.9")
        self.assertEqual(str(psm.get_param("[Vacuum] UserMode").string_value), "High vacuum")
        self.assertEqual(str(psm.get_param("[Vacuum] CHPressure").string_value), "1.589E-05 Torr (2.118E-05 mbar)")
        self.assertEqual(str(psm.get_param("[Detectors] Name").string_value), "TLD")
        self.assertEqual(str(psm.get_param("[TLD] Contrast").numerical_value), "68.1")
        self.assertEqual(str(psm.get_param("[TLD] Brightness").numerical_value), "51.6")
                

class SPCTagsTestCase(TestCase):

    def setUp(self):
        from django.contrib.auth.models import User
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

    def test_save_metadata(self):
        from os import path
        try:
            from tardis.apps.microtardis.filters.spctags import SPCTagsFilter
        except:
            raise SkipTest()

        exp = models.Experiment(title='exp: test spc filter',
                                institution_name='rmit',
                                approved=True,
                                created_by=self.user,
                                public=False)
        exp.save()
        logger.debug("experiment %s" % exp)
        
        self.assertEqual(exp.get_or_create_directory(),
                         path.join(settings.FILE_STORE_PATH, str(exp.id)))

        self.experiment_path = path.join(settings.FILE_STORE_PATH, str(exp.id))
      
        
        dataset = models.Dataset(description="dataset description...", experiment=exp)
        dataset.save()
        
        ## FEIQuanta200 TIF image testing ##
        filename = path.join(path.abspath(path.dirname(__file__)), 'testing/Quanta200/test.spc')
        logger.debug("filename %s" % filename)
 
        df_file = models.Dataset_File(dataset=dataset, filename='test.spc', url=filename, protocol='staging')
        df_file.save()

        #self.assertEqual("",models.Schema.objects.all())
        sch = models.Schema.objects.get(name="EDAXGenesis_SPC")
        self.assertEqual("EDAXGenesis_SPC",sch.name)
        datafileparameterset = models.DatafileParameterSet.objects.get(schema=sch, dataset_file=df_file)
        psm = ParameterSetManager(parameterset=datafileparameterset)
        self.assertEqual(10,len(psm.parameters))
        self.assertEqual(str(psm.get_param("Acc. Voltage").numerical_value), "19.981")
        self.assertEqual(str(psm.get_param("Peak ID Element 1").string_value), "Atomic=O, Line=K, Energy=0.5150, Height=2209")
        self.assertEqual(str(psm.get_param("Peak ID Element 2").string_value), "Atomic=Al, Line=K, Energy=1.4853, Height=6622")
        self.assertEqual(str(psm.get_param("Peak ID Element 3").string_value), "Atomic=Si, Line=K, Energy=1.7388, Height=491")
        self.assertEqual(str(psm.get_param("Peak ID Element 4").string_value), "Atomic=P, Line=K, Energy=2.0128, Height=160")
        self.assertEqual(str(psm.get_param("Peak ID Element 5").string_value), "Atomic=K, Line=K, Energy=3.3156, Height=124")
        self.assertEqual(str(psm.get_param("Peak ID Element 6").string_value), "Atomic=Mn, Line=K, Energy=5.8972, Height=1056")
        self.assertEqual(str(psm.get_param("Live Time").numerical_value), "120.0")
        self.assertEqual(str(psm.get_param("Time Constant").numerical_value), "120.0")
        self.assertEqual(str(psm.get_param("Sample Type (Label)").string_value), "sample 2 - 20 kv area")
        
        ## nanoSEM TIF image testing ##
        filename = path.join(path.abspath(path.dirname(__file__)), 'testing/NovaNanoSEM/test.spc')
        logger.debug("filename %s" % filename)
 
        df_file = models.Dataset_File(dataset=dataset, filename='test.spc', url=filename, protocol='staging')
        df_file.save()

        #self.assertEqual("",models.Schema.objects.all())
        sch = models.Schema.objects.get(name="EDAXGenesis_SPC")
        self.assertEqual("EDAXGenesis_SPC",sch.name)
        datafileparameterset = models.DatafileParameterSet.objects.get(schema=sch, dataset_file=df_file)
        psm = ParameterSetManager(parameterset=datafileparameterset)
        self.assertEqual(9,len(psm.parameters))
        self.assertEqual(str(psm.get_param("Acc. Voltage").numerical_value), "15.0")
        self.assertEqual(str(psm.get_param("Peak ID Element 1").string_value), "Atomic=C, Line=K, Energy=0.2660, Height=74078")
        self.assertEqual(str(psm.get_param("Peak ID Element 2").string_value), "Atomic=O, Line=K, Energy=0.5150, Height=2158")
        self.assertEqual(str(psm.get_param("Peak ID Element 3").string_value), "Atomic=Cu, Line=L, Energy=0.9316, Height=1760")
        self.assertEqual(str(psm.get_param("Peak ID Element 4").string_value), "Atomic=S, Line=K, Energy=2.3075, Height=1128")
        self.assertEqual(str(psm.get_param("Peak ID Element 5").string_value), "Atomic=Sb, Line=L, Energy=3.6041, Height=390")
        self.assertEqual(str(psm.get_param("Live Time").numerical_value), "343.9")
        self.assertEqual(str(psm.get_param("Time Constant").numerical_value), "500.0")
        self.assertEqual(str(psm.get_param("Sample Type (Label)").string_value), "Surface")
