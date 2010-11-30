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
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
from tardis.tardis_portal.models import Experiment

"""
tests.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Ulrich Felzmann <ulrich.felzmann@versi.edu.au>
.. moduleauthor::  Gerson Galang <gerson.galang@versi.edu.au>

"""
from django.test import TestCase
from django.test.client import Client

from tardis.tardis_portal.metsparser import MetsExperimentStructCreator
from tardis.tardis_portal.metsparser import MetsDataHolder
from tardis.tardis_portal.metsparser import MetsMetadataInfoHandler

from os import path
import unittest
from xml.sax.handler import feature_namespaces
from xml.sax import make_parser


class SearchTestCase(TestCase):

    fixtures = ['test_saxs_data']

    def setUp(self):
        self.client = Client()

    def testSearchDatafileForm(self):
        response = self.client.get('/search/datafile/', {'type': 'saxs', })

        # check if the response is a redirect to the login page
        self.assertRedirects(response,
            '/accounts/login/?next=/search/datafile/%3Ftype%3Dsaxs')

        # let's try to login this time...
        self.client.login(username='test', password='test')
        response = self.client.get('/search/datafile/', {'type': 'saxs', })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['searchForm'] is not None)
        self.assertTrue(response.context['searchDatafileSelectionForm'] is not
            None)
        self.assertTrue(response.context['modifiedSearchForm'] is not None)
        self.assertTemplateUsed(response,
            'tardis_portal/search_datafile_form.html')

        self.client.logout()

    def testSearchDatafileAuthentication(self):
        response = self.client.get('/search/datafile/',
                                   {'type': 'saxs', 'filename': '', })

        # check if the response is a redirect to the login page
        self.assertEqual(response.status_code, 302)

        # let's try to login this time...
        self.client.login(username='test', password='test')
        response = self.client.get('/search/datafile/',
            {'type': 'saxs', 'filename': '', })
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def testSearchDatafileResults(self):
        self.client.login(username='test', password='test')
        response = self.client.get('/search/datafile/',
            {'type': 'saxs', 'filename': 'air_0_001.tif', })

        # check for the existence of the contexts..
        self.assertTrue(response.context['datafiles'] is not None)
        self.assertTrue(response.context['paginator'] is not None)
        self.assertTrue(response.context['query_string'] is not None)
        self.assertTrue(response.context['subtitle'] is not None)
        self.assertTrue(response.context['nav'] is not None)
        self.assertTrue(response.context['bodyclass'] is not None)
        self.assertTrue(response.context['search_pressed'] is not None)
        self.assertTrue(response.context['searchDatafileSelectionForm'] is not
            None)

        self.assertEqual(len(response.context['paginator'].object_list), 1)
        self.assertTemplateUsed(response,
            'tardis_portal/search_datafile_results.html')

        from tardis.tardis_portal.models import Dataset_File
        self.assertTrue(
            type(response.context['paginator'].object_list[0]) is Dataset_File)

        # TODO: check if the schema is correct

        # check if searching for nothing would result to returning everything
        response = self.client.get('/search/datafile/',
            {'type': 'saxs', 'filename': '', })
        self.assertEqual(len(response.context['paginator'].object_list), 129)

        response = self.client.get('/search/datafile/',
            {'type': 'saxs', 'io': '123', })
        self.assertEqual(len(response.context['paginator'].object_list), 0)

        response = self.client.get('/search/datafile/',
            {'type': 'saxs', 'frqimn': '0.0450647', })
        self.assertEqual(len(response.context['paginator'].object_list), 125)
        self.client.logout()

    def testPrivateSearchFunctions(self):
        from tardis.tardis_portal import views

        # TODO: need to decide if we are to make those private functions public
        #       so they can be tested

    def testSearchExperimentForm(self):
        response = self.client.get('/search/experiment/')

        # check if the response is a redirect to the login page
        self.assertRedirects(response,
            '/accounts/login/?next=/search/experiment/')

        # let's try to login this time...
        self.client.login(username='test', password='test')
        response = self.client.get('/search/experiment/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['searchDatafileSelectionForm'] is not
            None)
        self.assertTemplateUsed(response,
            'tardis_portal/search_experiment_form.html')

        self.client.logout()

    def testSearchExperimentAuthentication(self):
        response = self.client.get('/search/experiment/',
            {'title': 'cookson', })

        # check if the response is a redirect to the login page
        self.assertEqual(response.status_code, 302)

        # let's try to login this time...
        self.client.login(username='test', password='test')
        response = self.client.get('/search/experiment/',
            {'title': 'cookson', })
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def testSearchExperimentResults(self):
        self.client.login(username='test', password='test')
        response = self.client.get('/search/experiment/',
            {'title': 'cookson'})

        # check for the existence of the contexts..
        self.assertTrue(response.context['experiments'] is not None)
        self.assertTrue(response.context['bodyclass'] is not None)
        self.assertTrue(response.context['searchDatafileSelectionForm'] is not
            None)

        self.assertTemplateUsed(response,
            'tardis_portal/search_experiment_results.html')

        self.assertTrue(
            len(response.context['experiments']) == 1)

        # check if searching for nothing would result to returning everything
        response = self.client.get('/search/experiment/',
            {'title': '', })
        self.assertEqual(len(response.context['experiments']), 3)

        self.client.logout()


# http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
class UserInterfaceTestCase(TestCase):

    def test_root(self):
        self.failUnlessEqual(Client().get('/').status_code, 200)

    def test_urls(self):
        c = Client()
        urls = ['/login', '/about', '/partners', '/stats']
        urls += ['/experiment/register', '/experiment/view']
        urls += ['/search/experiment', '/search/datafile?type=saxs']

        for u in urls:
            response = c.get(u)
            self.failUnlessEqual(response.status_code, 301)

    def test_login(self):
        from django.contrib.auth.models import User
        user = 'user2'
        pwd = 'test'
        email = ''
        User.objects.create_user(user, email, pwd)

        self.failUnlessEqual(self.client.login(username=user,
                             password=pwd), True)


class MetsExperimentStructCreatorTestCase(TestCase):

    def setUp(self):
        import os
        metsFile = os.path.join(path.abspath(path.dirname(__file__)),
            'tests/METS_test.xml')
        parser = make_parser(["drv_libxml2"])
        parser.setFeature(feature_namespaces, 1)
        self.dataHolder = MetsDataHolder()

        parser.setContentHandler(
            MetsExperimentStructCreator(self.dataHolder))
        parser.parse(metsFile)

    def testMetsStructMapContents(self):
        self.assertTrue(self.dataHolder.experimentDatabaseId == None,
            "experiment id shouldn't be set")
        self.assertTrue(len(self.dataHolder.metsStructMap) == 2,
            'metsStructMap size should be 2')

    def testMetsMetadataMapContents(self):
        self.assertTrue(len(self.dataHolder.metadataMap) == 7,
            'metadataMap size should be 7')
        self.assertTrue(self.dataHolder.metadataMap['A-2'].id == 'J-2',
            'id for metadata A-2 should be J-2')
        self.assertTrue(len(self.dataHolder.metadataMap['A-2'].datafiles) == 8,
            'there should be 8 datafiles within dataset A-2')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-2'].experiment.id == 'J-1',
            'id for dataset A-2 parent experiment should be J-1')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-2'].__class__.__name__ == 'Dataset',
            'metadata A-2 should be a Dataset type')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-1'].__class__.__name__ == 'Experiment',
            'metadata A-1 should be an Experiment type')
        self.assertTrue(len(self.dataHolder.metadataMap[
            'A-1'].datasets) == 1,
            'there should be 1 dataset under experiment A-1')
        self.assertTrue(self.dataHolder.metadataMap['A-7'].id == 'F-8',
            'metadata A-7 does not have F-8 as the Id')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-7'].name == 'ment0005.osc',
            'metadata A-7 should have ment0005.osc as the name')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-7'].url == 'file://Images/ment0005.osc',
            'metadata A-7 should have file://Images/ment0005.osc as the url')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-7'].dataset.id == 'J-2',
            'metadata A-7 should have dataset id J-2')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-7'].__class__.__name__ == 'Datafile',
            'metadata A-7 should be a Datafile type')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-7'].metadataId == 'A-7',
            'metadata A-7 should have metadata Id A-7')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-1'].metadataId == 'A-1',
            'metadata A-1 should have metadata Id A-1')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-2'].metadataId == 'A-2',
            'metadata A-2 should have metadata Id A-2')


class MetsMetadataInfoHandlerTestCase(TestCase):

    fixtures = ['test_saxs_data']

    def setUp(self):
        import os
        metsFile = os.path.join(path.abspath(path.dirname(__file__)),
            'tests/METS_test.xml')
        parser = make_parser(["drv_libxml2"])
        parser.setFeature(feature_namespaces, 1)
        self.dataHolder = MetsDataHolder()

        parser.setContentHandler(
            MetsExperimentStructCreator(self.dataHolder))
        parser.parse(metsFile)

        from django.contrib.auth.models import User
        self.user = User.objects.get(username='test')
        parser.setContentHandler(
            MetsMetadataInfoHandler(holder=self.dataHolder,
            tardisExpId=None,
            createdBy=self.user))
        parser.parse(metsFile)

    def testIngestedExperimentFields(self):
        self.assertTrue(self.dataHolder.experimentDatabaseId == 4,
            'Experiment ID should be 4')
        from tardis.tardis_portal import models
        experiment = models.Experiment.objects.get(id=4)
        self.assertTrue(experiment.title == 'SAXS Test',
            'wrong experiment title')
        self.assertTrue(experiment.institution_name ==
            'Adelaide University',
            'wrong experiment institution')
        self.assertTrue(experiment.description ==
            'Hello world hello world',
            'wrong experiment abstract')
        self.assertTrue(experiment.created_by == self.user,
            'wrong experiment creator')
        self.assertTrue(experiment.url ==
            'http://www.blahblah.com/espanol',
            'wrong experiment url')

        authors = models.Author_Experiment.objects.filter(
            experiment=experiment)
        self.assertTrue(len(authors) == 3)
        authorNames = [author.author.name for author in authors]
        self.assertTrue('Moscatto Brothers' in authorNames)

    def testIngestedDatasetFields(self):
        from tardis.tardis_portal import models
        experiment = models.Experiment.objects.get(id=4)
        datasets = models.Dataset.objects.filter(
            experiment=experiment)
        self.assertTrue(len(datasets) == 1,
            'there should only be one dataset for the experiment')
        dataset = datasets[0]
        self.assertTrue(dataset.description == 'Bluebird',
            'dataset description should be Bluebird')
        self.assertTrue(dataset.description == 'Bluebird',
            'dataset description should be Bluebird')

        datasetParams = models.DatasetParameter.objects.filter(
            parameterset__dataset=dataset)

        frlengParam = datasetParams.get(name__name='frleng')
        self.assertTrue(frlengParam.numerical_value == 554.619)

        frxcenParam = datasetParams.get(name__name='frxcen')
        self.assertTrue(frxcenParam.numerical_value == 411.947)

        frtypeParam = datasetParams.get(name__name='frtype')
        self.assertTrue(frtypeParam.string_value == 'PIL200K')

    def testIngestedDatafileFields(self):
        from tardis.tardis_portal import models
        dataset = models.Dataset.objects.get(description='Bluebird')
        datafiles = dataset.dataset_file_set.all()
        self.assertTrue(len(datafiles) == 5,
            'there should be 5 datafiles for the given dataset')
        datafile = datafiles.get(filename='ment0003.osc')
        self.assertTrue(datafile is not None,
            'datafile should not be none')
        self.assertTrue(datafile.size == '18006000',
            'wrong file size for ment0003.osc')

        datafileParams = models.DatafileParameter.objects.filter(
            parameterset__dataset_file=datafile)

        ioBgndParam = datafileParams.get(name__name='ioBgnd')
        self.assertTrue(ioBgndParam.numerical_value == 0)

        itParam = datafileParams.get(name__name='it')
        self.assertTrue(itParam.numerical_value == 288)

        positionerStrParam = datafileParams.get(name__name='positionerString')
        self.assertTrue(
            positionerStrParam.string_value == 'UDEF1_2_PV1_2_3_4_5')


class EquipmentTestCase(TestCase):

    fixtures = ['AS_Equipment.json']

    def setUp(self):
        self.client = Client()

    def testSearchEquipmentForm(self):
        response = self.client.get('/search/equipment/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'] is not None)

    def testSearchEquipmentResult(self):
        response = self.client.post('/search/equipment/', {'key': 'PIL', })
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
    userInterfaceSuite = \
        unittest.TestLoader().loadTestsFromTestCase(UserInterfaceTestCase)
    parserSuite1 = \
        unittest.TestLoader().loadTestsFromTestCase(
        MetsExperimentStructCreatorTestCase)
    parserSuite2 = \
        unittest.TestLoader().loadTestsFromTestCase(
        MetsMetadataInfoHandlerTestCase)
    searchSuite = \
        unittest.TestLoader().loadTestsFromTestCase(SearchTestCase)
    equipmentSuite = \
        unittest.TestLoader().loadTestsFromTestCase(EquipmentTestCase)
    allTests = unittest.TestSuite([parserSuite1,
                                   parserSuite2,
                                   userInterfaceSuite,
                                   searchSuite,
                                   equipmentSuite])
    return allTests
