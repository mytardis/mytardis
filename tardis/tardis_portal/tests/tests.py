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

from compare import expect, ensure
from os import path
import unittest
import datetime
from xml.sax.handler import feature_namespaces
from xml.sax import make_parser

from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User

from tardis.tardis_portal.models import *
from tardis.tardis_portal.views import _registerExperimentDocument
from tardis.tardis_portal.metsparser import MetsExperimentStructCreator
from tardis.tardis_portal.metsparser import MetsDataHolder
from tardis.tardis_portal.auth.localdb_auth import django_user, django_group

from tardis.apps.migration import TransferProvider

class SearchTestCase(TestCase):

    def setUp(self):
        # Load schemas for test
        from django.core.management import call_command
        call_command('loaddata', 'as_schemas')

        self.client = Client()
        self.experiments = []
        Location.force_initialize()

        try:
            user = User.objects.get(username='test')
        except User.DoesNotExist:
            user = User.objects.create_user('test', '', 'test')
            user.save()

        base_path = path.abspath(path.dirname(__file__))
        files = ['METS_test.xml']
        for f in files:
            filename = path.join(base_path, f)
            expid, _ = _registerExperimentDocument(filename=filename,
                                                   created_by=user,
                                                   expid=None)
            experiment = Experiment.objects.get(pk=expid)
            
            acl = ExperimentACL(pluginId=django_user,
                                entityId=str(user.id),
                                experiment=experiment,
                                canRead=True,
                                canWrite=True,
                                canDelete=True,
                                isOwner=True)
            acl.save()
            self.experiments += [experiment]

        schema = Schema.objects.get(type=Schema.DATAFILE, subtype='saxs')
        parameter = ParameterName.objects.get(schema=schema, name='io')
        parameter.is_searchable = True
        parameter.save()
        self.io_param_name = parameter.getUniqueShortName()

        schema = Schema.objects.get(type=Schema.DATASET, subtype='saxs')
        parameter = ParameterName.objects.get(schema=schema, name='frqimn')
        parameter.is_searchable = True
        parameter.save()
        self.frqimn_param_name = parameter.getUniqueShortName()

        new_schema = Schema()
        new_schema.namespace = 'testschemawithduplicatename'
        new_schema.save()
        new_param = ParameterName(
                        schema=new_schema,
                        name='title',
                        full_name='Duplicate title parametername',
                        is_searchable=True)
        new_param.save()


    def tearDown(self):
        for experiment in self.experiments:
            experiment.delete()

    def testSearchDatafileForm(self):
        self.client.login(username='test', password='test')
        response = self.client.get('/datafile/search/', {'type': 'saxs', })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['searchForm'] is not None)
        self.assertTrue(response.context['searchDatafileSelectionForm'] is not
            None)
        self.assertTrue(response.context['modifiedSearchForm'] is not None)
        self.assertTemplateUsed(response,
            'tardis_portal/search_datafile_form.html')

        self.client.logout()

    def testSearchDatafileAuthentication(self):
        response = self.client.get('/datafile/search/',
                                   {'type': 'saxs', 'filename': '', })

        # check if the response is zero since the user is not logged in
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['datafiles']), 0)

    def testSearchDatafileResults(self):
        login = self.client.login(username='test', password='test')
        self.assertEqual(login, True)
        response = self.client.get('/datafile/search/',
                                   {'type': 'saxs', 
                                    'filename': 'ment0005.osc', })

        # check for the existence of the contexts..
        self.assertTrue(response.context['datafiles'] is not None)
        self.assertTrue(response.context['experiments'] is not None)
        self.assertTrue(response.context['query_string'] is not None)
        self.assertTrue(response.context['subtitle'] is not None)
        self.assertTrue(response.context['nav'] is not None)
        self.assertTrue(response.context['bodyclass'] is not None)
        self.assertTrue(response.context['search_pressed'] is not None)
        self.assertTrue(response.context['searchDatafileSelectionForm'] is not
            None)

        #self.assertEqual(len(response.context['paginator'].object_list), 1)
        self.assertEqual(len(response.context['datafiles']), 1)
        self.assertEqual(len(response.context['experiments']), 1)
        self.assertTemplateUsed(response,
            'tardis_portal/search_experiment_results.html')

        from tardis.tardis_portal.models import Dataset_File
        from tardis.tardis_portal.models import Experiment

        values = response.context['experiments']
        experiment = values[0]
        datafile = response.context['datafiles'][0]
        self.assertTrue(
            type(experiment['sr']) is Experiment)
        self.assertTrue(
            type(datafile) is Dataset_File)


        self.assertTrue(experiment['dataset_file_hit'] is True)
        self.assertTrue(experiment['dataset_hit'] is False)
        self.assertTrue(experiment['experiment_hit'] is False)

        # TODO: check if the schema is correct

        # check if searching for nothing would result to returning everything
        response = self.client.get('/datafile/search/',
                                   {'type': 'saxs', 'filename': '', })
        self.assertEqual(len(response.context['datafiles']), 5)

        response = self.client.get('/datafile/search/',
            {'type': 'saxs',  self.io_param_name: '123', })
        self.assertEqual(len(response.context['datafiles']), 0)

        response = self.client.get('/datafile/search/',
            {'type': 'saxs', self.frqimn_param_name: '0.0450647', })
        self.assertEqual(len(response.context['datafiles']), 5)
        self.client.logout()

    def testSearchExperimentForm(self):
        login = self.client.login(username='test', password='test')
        self.assertEqual(login, True)
        response = self.client.get('/experiment/search/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['searchDatafileSelectionForm'] is not
            None)
        self.assertTemplateUsed(response,
            'tardis_portal/search_experiment_form.html')
        self.client.logout()

    def testSearchExperimentAuthentication(self):
        self.client.login(username='test', password='test')
        response = self.client.get('/experiment/search/',
            {'title': 'cookson', })
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def testSearchExperimentResults(self):
        self.client.login(username='test', password='test')
        response = self.client.get('/experiment/search/',
            {'title': 'SAXS Test'})

        # check for the existence of the contexts..
        self.assertTrue(response.context['experiments'] is not None)
        self.assertTrue(response.context['bodyclass'] is not None)
        self.assertTrue(response.context['searchDatafileSelectionForm'] is not
            None)

        self.assertTemplateUsed(response,
            'tardis_portal/search_experiment_results.html')

        self.assertEqual(len(response.context['experiments']), 1)

        from tardis.tardis_portal.models import Experiment

        values = response.context['experiments']
        experiment = values[0]

        self.assertTrue(
            type(experiment['sr']) is Experiment)

        self.assertTrue(experiment['dataset_file_hit'] is False)
        self.assertTrue(experiment['dataset_hit'] is False)
        self.assertTrue(experiment['experiment_hit'] is True)

        # check if searching for nothing would result to returning everything
        response = self.client.get('/experiment/search/',
            {'title': '', })
        self.assertEqual(len(response.context['experiments']), 1)

        self.client.logout()


# http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
class UserInterfaceTestCase(TestCase):

    def test_root(self):
        ensure(Client().get('/').status_code, 200)

    def test_urls(self):
        c = Client()
        urls = [ '/login/', '/about/', '/stats/', \
                 '/experiment/register/', '/experiment/list/public', \
                 '/experiment/search/' ]

        for u in urls:
            response = c.get(u)
            expect(response.status_code).to_equal(200)

        redirect_urls = [ '/experiment/list', '/experiment/view/' ]

        for u in redirect_urls:
            response = c.get(u)
            expect(response.status_code).to_equal(302)


    def test_urls_with_some_content(self):
        # Things that might tend to be in a real live system
        user = 'testuser'
        pwd = User.objects.make_random_password()
        user = User.objects.create(username=user, email='testuser@example.test',
                                   first_name="Test", last_name="User")
        user.set_password(pwd)
        user.save()
        UserProfile(user=user).save()
        experiment = Experiment.objects.create(title="Test Experiment",
                                               created_by=user,
                                               public_access= \
                                                 Experiment.PUBLIC_ACCESS_FULL)
        experiment.save()
        acl = ExperimentACL(pluginId=django_user,
                            entityId=str(user.id),
                            experiment=experiment,
                            canRead=True,
                            canWrite=True,
                            canDelete=True,
                            isOwner=True)
        acl.save()
        dataset = Dataset(description="test dataset")
        dataset.save()
        dataset.experiments.add(experiment)
        dataset.save()


        # Test everything works
        c = Client()
        c.login(username=user, password=pwd)
        urls = [ '/about/', '/stats/']
        urls += [ '/experiment/list/%s' % part
                    for part in ('mine', 'shared', 'public')]
        urls += [ '/experiment/%s/' % part \
                    for part in ('register', 'search') ]
        urls += [ '/experiment/view/%d/' % experiment.id ]
        urls += [ '/ajax/experiment/%d/%s' % (experiment.id, tabpane) \
                    for tabpane in ('description', 'datasets', 'rights') ]
        urls += [ '/ajax/datafile_list/%d/' % dataset.id ]
        urls += [ '/ajax/dataset_metadata/%d/' % dataset.id ]

        for u in urls:
            response = c.get(u)
            ensure(response.status_code, 200,
                   "%s should have returned 200 but returned %d"\
                   % (u, response.status_code))

        redirect_urls = [ '/experiment/list', '/experiment/view/' ]

        for u in redirect_urls:
            response = c.get(u)
            expect(response.status_code).to_equal(302)

    def test_search_urls(self):
        # Load schemas for test
        from django.core.management import call_command
        call_command('loaddata', 'as_schemas')

        c = Client()
        urls = ('/datafile/search/?type='+x for x in ['mx','ir','saxs'])

        for u in urls:
            response = c.get(u)
            print str(response)
            ensure(response.status_code, 200)


    def test_login(self):
        from django.contrib.auth.models import User
        user = 'user2'
        pwd = 'test'
        email = ''
        User.objects.create_user(user, email, pwd)

        ensure(self.client.login(username=user, password=pwd), True)


class MetsExperimentStructCreatorTestCase(TestCase):

    def setUp(self):
        import os
        metsFile = os.path.join(path.abspath(path.dirname(__file__)),
            './METS_test.xml')
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
        self.assertTrue(self.dataHolder.metadataMap['A-2'][0].id == 'J-2',
            'id for metadata A-2 should be J-2')
        self.assertTrue(len(self.dataHolder.metadataMap['A-2'][0].datafiles) == 8,
            'there should be 8 datafiles within dataset A-2')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-2'][0].experiment.id == 'J-1',
            'id for dataset A-2 parent experiment should be J-1')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-2'][0].__class__.__name__ == 'Dataset',
            'metadata A-2 should be a Dataset type')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-1'][0].__class__.__name__ == 'Experiment',
            'metadata A-1 should be an Experiment type')
        self.assertTrue(len(self.dataHolder.metadataMap[
            'A-1'][0].datasets) == 1,
            'there should be 1 dataset under experiment A-1')
        self.assertTrue(self.dataHolder.metadataMap['A-7'][0].id == 'F-8',
            'metadata A-7 does not have F-8 as the Id')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-7'][0].name == 'ment0005.osc',
            'metadata A-7 should have ment0005.osc as the name')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-7'][0].url == 'Images/ment0005.osc',
            'metadata A-7 should have tardis://Images/ment0005.osc as the url')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-7'][0].dataset.id == 'J-2',
            'metadata A-7 should have dataset id J-2')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-7'][0].__class__.__name__ == 'Datafile',
            'metadata A-7 should be a Datafile type')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-7'][0].metadataIds[0] == 'A-7',
            'metadata A-7 should have metadata Id A-7')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-1'][0].metadataIds[0] == 'A-1',
            'metadata A-1 should have metadata Id A-1')
        self.assertTrue(self.dataHolder.metadataMap[
            'A-2'][0].metadataIds[0] == 'A-2',
            'metadata A-2 should have metadata Id A-2')


class MetsMetadataInfoHandlerTestCase(TestCase):

    def setUp(self):
        # Load schemas for test
        from django.core.management import call_command
        call_command('loaddata', 'as_schemas')
        self.experiment = None
        Location.force_initialize()

        try:
            self.user = User.objects.get(username='test')
        except User.DoesNotExist:
            self.user = User.objects.create_user('test', '', 'test')
            self.user.save()

        filename = path.join(path.abspath(path.dirname(__file__)),
                             './METS_test.xml')

        expid, sync_path = _registerExperimentDocument(filename,
                                                       self.user,
                                                       expid=None)
        ensure(sync_path.startswith(settings.SYNC_TEMP_PATH), True,
               "Sync path should be influenced by SYNC_TEMP_PATH: %s" %
               sync_path)
        self.experiment = Experiment.objects.get(pk=expid)
        self.sync_path = sync_path

    def tearDown(self):
        self.experiment.delete()

    def testIngestedExperimentFields(self):
        from tardis.tardis_portal import models
        self.assertTrue(self.experiment.title == 'SAXS Test',
            'wrong experiment title')
        self.assertTrue(self.experiment.institution_name ==
            'Adelaide University',
            'wrong experiment institution')
        self.assertTrue(self.experiment.description ==
            'Hello world hello world',
            'wrong experiment abstract')
        self.assertTrue(self.experiment.created_by == self.user,
            'wrong experiment creator')
        self.assertTrue(self.experiment.url ==
            'http://www.blahblah.com/espanol',
            'wrong experiment url')
        self.assertEqual(self.experiment.start_time,
            datetime.datetime(2011, 12, 31, 13, 55))
        self.assertEqual(self.experiment.end_time,
            datetime.datetime(2035, 11, 29, 14, 33))

        authors = models.Author_Experiment.objects.filter(
            experiment=self.experiment)
        self.assertTrue(len(authors) == 3)
        authorNames = [author.author for author in authors]
        self.assertTrue('Moscatto Brothers' in authorNames)

    def testIngestedDatasetFields(self):
        from tardis.tardis_portal import models
        datasets = self.experiment.datasets.all()
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
        import hashlib
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
        replica = datafile.get_preferred_replica()
        expect(replica.url).to_equal('file://'+path.join(self.sync_path,
                                                        'Images/ment0003.osc'))

        datafileParams = models.DatafileParameter.objects.filter(
            parameterset__dataset_file=datafile)

        ioBgndParam = datafileParams.get(name__name='ioBgnd')
        self.assertTrue(ioBgndParam.numerical_value == 0)

        itParam = datafileParams.get(name__name='it')
        self.assertTrue(itParam.numerical_value == 288)

        positionerStrParam = datafileParams.get(name__name='positionerString')
        self.assertTrue(
            positionerStrParam.string_value == 'UDEF1_2_PV1_2_3_4_5')

        # Check MD5 works
        self.assertTrue(datafile.md5sum == 'deadbeef' \
                        * (hashlib.md5('').digest_size / 4),
            'wrong MD5 hash for ment0003.osc')

        # Check SHA-512 works
        datafile = datafiles.get(filename='ment0005.osc')
        self.assertTrue(datafile.sha512sum == 'deadbeef' \
                        * (hashlib.sha512('').digest_size / 4),
            'wrong SHA-512 hash for ment0005.osc')

    def testMetsExport(self):
        client = Client()
        response = client.login(username='test', password='test')
        expid = self.experiment.id
        response = client.get('/experiment/metsexport/%i/' % expid)
        self.assertEqual(response.status_code, 403)
        self.experiment.public_access = Experiment.PUBLIC_ACCESS_FULL
        self.experiment.save()
        response = client.get('/experiment/metsexport/%i/' % expid)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="mets_expid_%s.xml"' % expid)


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

    allTests = unittest.TestSuite([parserSuite1,
                                   parserSuite2,
                                   userInterfaceSuite,
                                   searchSuite,
                                   equipmentSuite,
                                   ])
    return allTests
