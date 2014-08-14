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

from tardis.tardis_portal.models import UserProfile, Experiment, ObjectACL, \
    Schema, ParameterName, Dataset
from tardis.tardis_portal.auth.localdb_auth import django_user


class SearchTestCase(TestCase):

    def setUp(self):
        # Load schemas for test
        from django.core.management import call_command
        call_command('loaddata', 'as_schemas')

        self.client = Client()
        self.experiments = []

        try:
            user = User.objects.get(username='test')
        except User.DoesNotExist:
            user = User.objects.create_user('test', '', 'test')
            user.save()

        self.userprofile = UserProfile(user=user).save()

        base_path = path.abspath(path.dirname(__file__))
        experiment = Experiment(title='SAXS Test',
                                created_by=user)
        experiment.save()

        acl = ObjectACL(pluginId=django_user,
                        entityId=str(user.id),
                        content_object=experiment,
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

    # def testSearchDatafileResults(self):
    #     login = self.client.login(username='test', password='test')
    #     self.assertEqual(login, True)
    #     response = self.client.get('/datafile/search/',
    #                                {'type': 'saxs',
    #                                 'filename': 'ment0005.osc', })
    #
    #     # check for the existence of the contexts..
    #     self.assertTrue(response.context['datafiles'] is not None)
    #     self.assertTrue(response.context['experiments'] is not None)
    #     self.assertTrue(response.context['query_string'] is not None)
    #     self.assertTrue(response.context['subtitle'] is not None)
    #     self.assertTrue(response.context['nav'] is not None)
    #     self.assertTrue(response.context['bodyclass'] is not None)
    #     self.assertTrue(response.context['search_pressed'] is not None)
    #     self.assertTrue(response.context['searchDatafileSelectionForm']
    #         is not None)
    #
    #     #self.assertEqual(len(response.context['paginator'].object_list), 1)
    #     self.assertEqual(len(response.context['datafiles']), 1)
    #     self.assertEqual(len(response.context['experiments']), 1)
    #     self.assertTemplateUsed(response,
    #         'tardis_portal/search_experiment_results.html')
    #
    #     from tardis.tardis_portal.models import DataFile
    #     from tardis.tardis_portal.models import Experiment
    #
    #     values = response.context['experiments']
    #     experiment = values[0]
    #     datafile = response.context['datafiles'][0]
    #     self.assertTrue(
    #         type(experiment['sr']) is Experiment)
    #     self.assertTrue(
    #         type(datafile) is DataFile)
    #
    #     self.assertTrue(experiment['datafile_hit'] is True)
    #     self.assertTrue(experiment['dataset_hit'] is False)
    #     self.assertTrue(experiment['experiment_hit'] is False)
    #
    #     # TODO: check if the schema is correct
    #
    #     # check if searching for nothing would result to returning everything
    #     response = self.client.get('/datafile/search/',
    #                                {'type': 'saxs', 'filename': '', })
    #     self.assertEqual(len(response.context['datafiles']), 5)
    #
    #     response = self.client.get('/datafile/search/',
    #         {'type': 'saxs',  self.io_param_name: '123', })
    #     self.assertEqual(len(response.context['datafiles']), 0)
    #
    #     response = self.client.get('/datafile/search/',
    #         {'type': 'saxs', self.frqimn_param_name: '0.0450647', })
    #     self.assertEqual(len(response.context['datafiles']), 5)
    #     self.client.logout()

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

        self.assertTrue(experiment['datafile_hit'] is False)
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
        urls = ['/login/', '/about/', '/stats/',
                '/experiment/list/public',
                '/experiment/search/']

        for u in urls:
            response = c.get(u)
            expect(response.status_code).to_equal(200)

        redirect_urls = ['/experiment/list', '/experiment/view/']

        for u in redirect_urls:
            response = c.get(u)
            expect(response.status_code).to_equal(302)

    def test_urls_with_some_content(self):
        # Things that might tend to be in a real live system
        user = 'testuser'
        pwd = User.objects.make_random_password()
        user = User.objects.create(username=user,
                                   email='testuser@example.test',
                                   first_name="Test", last_name="User")
        user.set_password(pwd)
        user.save()
        UserProfile(user=user).save()
        experiment = Experiment.objects.create(title="Test Experiment",
                                               created_by=user,
                                               public_access=
                                               Experiment.PUBLIC_ACCESS_FULL)
        experiment.save()
        acl = ObjectACL(pluginId=django_user,
                        entityId=str(user.id),
                        content_object=experiment,
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
        urls = ['/about/', '/stats/']
        urls += ['/experiment/list/%s' % part
                 for part in ('mine', 'shared', 'public')]
        urls += ['/experiment/%s/' % part
                 for part in ('search',)]
        urls += ['/experiment/view/%d/' % experiment.id]
        urls += ['/ajax/experiment/%d/%s' % (experiment.id, tabpane)
                 for tabpane in ('description', 'datasets', 'rights')]
        urls += ['/ajax/datafile_list/%d/' % dataset.id]
        urls += ['/ajax/dataset_metadata/%d/' % dataset.id]

        for u in urls:
            response = c.get(u)
            ensure(response.status_code, 200,
                   "%s should have returned 200 but returned %d"
                   % (u, response.status_code))

        redirect_urls = ['/experiment/list', '/experiment/view/']

        for u in redirect_urls:
            response = c.get(u)
            expect(response.status_code).to_equal(302)

    def test_search_urls(self):
        # Load schemas for test
        from django.core.management import call_command
        call_command('loaddata', 'as_schemas')

        c = Client()
        urls = ('/datafile/search/?type='+x for x in ['mx', 'ir', 'saxs'])

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


def suite():
    userInterfaceSuite = \
        unittest.TestLoader().loadTestsFromTestCase(UserInterfaceTestCase)
    # parserSuite1 = \
    #     unittest.TestLoader().loadTestsFromTestCase(
    #     MetsExperimentStructCreatorTestCase)
    # parserSuite2 = \
    #     unittest.TestLoader().loadTestsFromTestCase(
    #     MetsMetadataInfoHandlerTestCase)
    # searchSuite = \
    #     unittest.TestLoader().loadTestsFromTestCase(SearchTestCase)

    allTests = unittest.TestSuite([
        # parserSuite1,
        # parserSuite2,
        userInterfaceSuite,
        # searchSuite,
        # equipmentSuite,
    ])
    return allTests
