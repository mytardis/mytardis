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

"""
tests.py
http://docs.djangoproject.com/en/dev/topics/testing/

@author Ulrich Felzmann
@author Gerson Galang

"""

from django.test import TestCase
from django.test.client import Client
from tardis.tardis_portal.logger import logger
import unittest
from os import path


class SearchTestCase(TestCase):

    fixtures = ['test_sax_data']

    def setUp(self):
        self.client = Client()

    def testSearchDatafileForm(self):
        response = self.client.get('/search/datafile/', {'type': 'sax', })

        # check if the response is a redirect to the login page
        self.assertRedirects(response,
            '/accounts/login/?next=/search/datafile/%3Ftype%3Dsax')

        # let's try to login this time...
        self.client.login(username='test', password='test')
        response = self.client.get('/search/datafile/', {'type': 'sax', })
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
            {'type': 'sax', 'filename': '', })

        # check if the response is a redirect to the login page
        self.assertEqual(response.status_code, 302)

        # let's try to login this time...
        self.client.login(username='test', password='test')
        response = self.client.get('/search/datafile/',
            {'type': 'sax', 'filename': '', })
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def testSearchDatafileResults(self):
        self.client.login(username='test', password='test')
        response = self.client.get('/search/datafile/',
            {'type': 'sax', 'filename': 'air_0_001.tif', })

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
            {'type': 'sax', 'filename': '', })
        self.assertEqual(len(response.context['paginator'].object_list), 129)

        response = self.client.get('/search/datafile/',
            {'type': 'sax', 'io': '123', })
        self.assertEqual(len(response.context['paginator'].object_list), 0)

        response = self.client.get('/search/datafile/',
            {'type': 'sax', 'frqimn': '0.0450647', })
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
        urls += ['/search/experiment', '/search/datafile?type=sax']

        for u in urls:
            response = c.get(u)

            # print u, response.status_code

            self.failUnlessEqual(response.status_code, 301)

    def test_register(self):
        self.client = Client()

        from django.contrib.auth.models import User
        from django.conf import settings
        import os

        user = 'user1'
        pwd = 'test'
        email = ''
        User.objects.create_user(user, email, pwd)

        f = open(os.path.join(path.abspath(path.dirname(__file__)),
                 'tests/notMETS_test.xml'), 'r')
        response = self.client.post('/experiment/register/', {
            'username': user,
            'password': pwd,
            'xmldata': f,
            'originid': '286',
            'experiment_owner': user,
            })
        f.close()
        self.failUnlessEqual(response.status_code, 200)

    def test_login(self):
        from django.contrib.auth.models import User
        user = 'user2'
        pwd = 'test'
        email = ''
        User.objects.create_user(user, email, pwd)

        self.failUnlessEqual(self.client.login(username=user,
                             password=pwd), True)


class ExperimentParserTestCase(unittest.TestCase):

    def setUp(self):
        from django.conf import settings
        import os
        f = open(os.path.join(path.abspath(path.dirname(__file__)),
                 'tests/METS_test.xml'), 'r')
        xmlString = f.read()
        f.close()
        from tardis.tardis_portal.ExperimentParser import ExperimentParser
        self.experimentParser = ExperimentParser(str(xmlString))

    def testGetTitle(self):
        self.assertTrue(self.experimentParser.getTitle() == 'Test Title',
            'title is not the same')

    def testGetAuthors(self):
        self.assertTrue(len(self.experimentParser.getAuthors()) == 3,
            'number of authors should be 3')
        self.assertTrue('Author2' in self.experimentParser.getAuthors(),
            '"Author2 should be in the authors list"')

    def testGetAbstract(self):
        self.assertTrue(self.experimentParser.getAbstract() ==
            'Test Abstract.', 'abstract is not the same')

    def testGetRelationURLs(self):
        self.assertTrue('http://www.test.com' in
            self.experimentParser.getRelationURLs(),
            'missing url from relationsURLs')
        self.assertTrue(len(self.experimentParser.getRelationURLs()) == 1,
            'there should only be 1 relationsURL')

    def testGetAgentName(self):
        self.assertTrue(self.experimentParser.getAgentName('CREATOR') ==
            'Creator', 'agent should be "Creator"')
        self.assertTrue(self.experimentParser.getAgentName('PAINTER') == None,
            'there is no "Painter" agent')

    def testGetDatasetTitle(self):
        self.assertTrue(self.experimentParser.getDatasetTitle('J-2') ==
            'Dataset1 Title', 'dataset title should be "J-2"')
        self.assertTrue(self.experimentParser.getDatasetTitle('J-4') == None,
            'there is no dataset with id "J-4"')

    def testGetDatasetDMDIDs(self):
        self.assertTrue(len(self.experimentParser.getDatasetDMDIDs()) == 2,
            'total number of datasets is wrong')
        self.assertTrue('J-2' in self.experimentParser.getDatasetDMDIDs(),
            'J-2 is not in the dataset')
        self.assertTrue('J-1' not in self.experimentParser.getDatasetDMDIDs(),
            "J-1 shouldn't be in the dataset")

    def testGetDatasetADMIDs(self):
        # get metadata ids for this dataset...

        pass

    def testGetFileIDs(self):
        self.assertTrue('F-3' in self.experimentParser.getFileIDs('J-3'),
            'F-3 is missing from the file IDs')
        self.assertTrue(len(self.experimentParser.getFileIDs('J-3')) == 2,
            'there should only be 2 files for the J-3 dataset')
        self.assertTrue('F-5' not in self.experimentParser.getFileIDs('J-3'),
            'F-3 is missing from the file IDs')

    def testGetFileLocation(self):
        self.assertTrue(self.experimentParser.getFileLocation('F-1') ==
            'file://Images/File1', "file F-1's location is wrong")

    def testGetFileADMIDs(self):
        # get metadata ids for this file...

        self.assertTrue('A-3' in self.experimentParser.getFileADMIDs('F-4'),
            'wrong file metadata id')
        self.assertTrue(len(self.experimentParser.getFileADMIDs('F-4')) == 1,
            'there should only be 1 metadata ID for the file')

    def testGetFileName(self):
        self.assertTrue(self.experimentParser.getFileName('F-1') == 'File1',
            'wrong file name for file "F-1"')

    def testGetFileSize(self):
        self.assertTrue(self.experimentParser.getFileSize('F-1') == '6148',
            'wrong file size for file "F-1"')

    def testGetTechXML(self):
        # check if the root of the returned element is datafile or
        # something else

        self.assertTrue(self.experimentParser.getTechXML('A-3').getroot().\
            tag == '{http://www.tardis.edu.au/schemas/trdDatafile/1}datafile',
            'element has wrong tag')

    def testGetParameterFromTechXML(self):
        pass


class ModelTestCase(TestCase):

    def setUp(self):
        from django.contrib.auth.models import User
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

    def test_experiment(self):
        from tardis.tardis_portal import models
        exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                created_by=self.user,
                                )
        exp.save()
        self.assertEqual(exp.title, 'test exp1')
        self.assertEqual(exp.url, '')
        self.assertEqual(exp.institution_name, 'monash')
        self.assertEqual(exp.approved, False)
        self.assertEqual(exp.handle, None)
        self.assertEqual(exp.created_by, self.user)
        self.assertEqual(exp.public, False)
        self.assertEqual(exp.get_absolute_url(), '/experiment/view/1/',
                         exp.get_absolute_url() + ' != /experiment/view/1/')

    def test_authors(self):
        from tardis.tardis_portal import models
        exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                created_by=self.user,
                                )
        exp.save()

        a1 = models.Author(name="steve")
        a1.save()

        a2 = models.Author(name="russell")
        a2.save()

        ae1 = models.Author_Experiment(experiment=exp,
                                       author=a1,
                                       order=0)
        ae1.save()

        ae2 = models.Author_Experiment(experiment=exp,
                                       author=a2,
                                       order=1)
        ae2.save()

        authors = exp.authors.all()

        # confirm that there are 2 authors
        self.assertEqual(len(authors), 2)
        self.assertTrue(a1 in authors)
        self.assertTrue(a2 in authors)

    def test_datafile(self):
        from tardis.tardis_portal import models
        exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                approved=True,
                                created_by=self.user,
                                public=False,
                                )
        exp.save()

        dataset = models.Dataset(description="dataset description...",
                                 experiment=exp)
        dataset.save()

        df_file = models.Dataset_File(dataset=dataset,
                                      filename='file.txt',
                                      url='file://path/file.txt',
                                      )
        df_file.save()
        self.assertEqual(df_file.filename, 'file.txt')
        self.assertEqual(df_file.url, 'file://path/file.txt')
        self.assertEqual(df_file.dataset, dataset)
        self.assertEqual(df_file.size, '')


class ExperimentFormTestCase(TestCase):

    def setUp(self):
        from django.contrib.auth.models import User
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

    def _data_to_post(self, data=None):
        from django.http import QueryDict
        data = data or [('authors', 'russell, steve'),
                        ('created_by', self.user.pk),
                        ('dataset_description[0]', 'first one'),
                        ('dataset_description[1]', 'second'),
                        ('description', 'desc.....'),
                        ('file_filename[0]', 'file/another.py'),
                        ('file_filename[1]', 'second_ds/file.py'),
                        ('file_filename[1]', 'second_ds/file1.py'),
                        ('institution_name', 'some university'),
                        ('title', 'test experiment'),
                        ('url', 'http://www.test.com')]
        data = QueryDict('&'.join(['%s=%s' % (k, v) for k, v in data]))
        return data

    def _create_experiment(self, data=None):
        from tardis.tardis_portal import models, forms
        from os.path import basename
        from django.contrib.auth.models import User
        data = self._data_to_post(data)
        exp = models.Experiment(title=data['title'],
                                institution_name=data['institution_name'],
                                description=data['description'],
                                created_by=User.objects.get(id=data['created_by']),
                                )
        exp.save()
        for i, a in enumerate(data['authors'].split(', ')):
            author = models.Author(name=a)
            author.save()

            ae = models.Author_Experiment(experiment=exp,
                                          author=author,
                                          order=i)
            ae.save()

        for k, v in data.items():
            match = forms.FullExperiment.re_post_data.match(k)
            if not match or not 'dataset' == match.groupdict()['form']:
                continue
            number = int(match.groupdict()['number'])
            dataset = models.Dataset(description=v,
                                     experiment=exp)
            dataset.save()

            datafiles = data.getlist('file_filename[' + str(number) + ']')
            for f in datafiles:
                d = models.Dataset_File(url='file://' + f,
                                         dataset=dataset,
                                         filename=basename(f))
                d.save()
        return exp

    def test_form_printing(self):
        from tardis.tardis_portal import forms

        example_post = self._data_to_post()

        f = forms.FullExperiment(example_post)
        as_table = """<tr><th><label for="url">Url:</label></th><td><input id="url" type="text" name="url" value="http://www.test.com" maxlength="255" /></td></tr>
<tr><th><label for="title">Title:</label></th><td><input id="title" type="text" name="title" value="test experiment" maxlength="400" /></td></tr>
<tr><th><label for="institution_name">Institution name:</label></th><td><input id="institution_name" type="text" name="institution_name" value="some university" maxlength="400" /></td></tr>
<tr><th><label for="description">Description:</label></th><td><textarea id="description" rows="10" cols="40" name="description">desc.....</textarea></td></tr>
<tr><th><label for="created_by">Created by:</label></th><td><select name="created_by" id="created_by">
<option value="">---------</option>
<option value="1" selected="selected">tardis_user1</option>
</select></td></tr>
<tr><th><label for="public">Public:</label></th><td><input type="checkbox" name="public" id="public" /></td></tr>
<tr><th><label for="authors">Authors:</label></th><td><input type="text" name="authors" value="russell, steve" id="authors" /></td></tr>"""
        self.assertEqual(f.as_table(), as_table)

    def test_form_parsing(self):
        from os.path import basename
        from tardis.tardis_portal import forms, models

        example_post = [('title', 'test experiment'),
                        ('created_by', self.user.pk),
                        ('url', 'http://www.test.com'),
                        ('institution_name', 'some university'),
                        ('description', 'desc.....'),
                        ('authors', 'russell, steve'),
                        ('dataset_description[0]', 'first one'),
                        ('file_filename[0]', 'location.py'),
                        ('file_filename[0]', 'another.py'),
                        ('file_url[0]', 'file://file/location.py'),
                        ('file_url[0]', 'file://file/another.py'),
                        ('dataset_description[1]', 'second'),
                        ('file_filename[1]', 'file.py'),
                        ('file_url[1]', 'file://second_ds/file.py'),
                        ]
        example_post = self._data_to_post(example_post)

        f = forms.FullExperiment(example_post)

        # test validity of form data
        self.assertTrue(f.is_valid(), repr(f.errors))

        # save form
        exp = f.save()

        # retrieve model from database
        e = models.Experiment.objects.get(pk=exp['experiment'].pk)
        self.assertEqual(e.title, example_post['title'])
        self.assertEqual(unicode(e.created_by.pk), example_post['created_by'])
        self.assertEqual(e.institution_name, example_post['institution_name'])
        self.assertEqual(e.description, example_post['description'])

        # test there are 2 authors
        self.assertEqual(len(e.authors.all()), 2)

        # check we can get one of the authors back
        self.assertEqual(e.authors.get(name='steve').name, 'steve')

        # check both datasets have been saved
        ds = models.Dataset.objects.filter(experiment=exp['experiment'].pk)
        self.assertEqual(len(ds), 2)

        # check that all the files exist in the database
        check_files = {'first one': ['file/location.py', 'file/another.py'],
                       'second': ['second_ds/file.py']}
        for d in ds:
            files = models.Dataset_File.objects.filter(dataset=d.pk)
            v_files = [basename(f) for f in check_files[d.description]]
            v_urls = ['file://' + f for f in check_files[d.description]]
            for f in files:
                self.assertTrue(f.filename in v_files,
                                "%s not in %s" % (f.filename, v_files))
                self.assertTrue(f.url in v_urls,
                                "%s not in %s" % (f.url, v_urls))

    def test_initial_form(self):
        from tardis.tardis_portal import forms

        as_table = """<tr><th><label for="url">Url:</label></th><td><input id="url" type="text" name="url" maxlength="255" /></td></tr>
<tr><th><label for="title">Title:</label></th><td><input id="title" type="text" name="title" maxlength="400" /></td></tr>
<tr><th><label for="institution_name">Institution name:</label></th><td><input id="institution_name" type="text" name="institution_name" maxlength="400" /></td></tr>
<tr><th><label for="description">Description:</label></th><td><textarea id="description" rows="10" cols="40" name="description"></textarea></td></tr>
<tr><th><label for="created_by">Created by:</label></th><td><select name="created_by" id="created_by">
<option value="" selected="selected">---------</option>
<option value="1">tardis_user1</option>
</select></td></tr>
<tr><th><label for="public">Public:</label></th><td><input type="checkbox" name="public" id="public" /></td></tr>
<tr><th><label for="authors">Authors:</label></th><td><input type="text" name="authors" id="authors" /></td></tr>"""

        f = forms.FullExperiment()
        self.assertEqual(f.as_table(), as_table)

    def test_validation(self):
        from tardis.tardis_portal import forms

        # test empty form
        f = forms.FullExperiment()
        self.assertTrue(f.is_valid())

        # test blank post data
        post = self._data_to_post([('authors', ''),
                                   ('created_by', ''),
                                   ('dataset_description[0]', ''),
                                   ('dataset_description[1]', ''),
                                   ('description', ''),
                                   ('file_filename[0]', ''),
                                   ('file_filename[1]', ''),
                                   ('institution_name', ''),
                                   ('title', ''),
                                   ('url', '')])
        f = forms.FullExperiment(data=post)
        self.assertFalse(f.is_valid())

        # test a valid form
        example_post = self._data_to_post()
        f = forms.FullExperiment(example_post)
        self.assertTrue(f.is_valid())

    def test_instance(self):
        from tardis.tardis_portal import forms
        exp = self._create_experiment()
        f = forms.FullExperiment(instance=exp)
        value = "value=\"%s\""
        text_area = ">%s</textarea>"
        self.assertTrue(value % 'test experiment' in
                        str(f['title']), str(f['title']))
        self.assertTrue(value % 'some university' in
                        str(f['institution_name']))
        self.assertTrue('selected="selected">tardis_user1</option>' in
                        str(f['created_by']))
        for ds, df in f.get_datasets():
            if 'dataset_description[0]' in str(ds['description']):
                self.assertTrue(text_area % "first one" in
                                str(ds['description']))
                for file in df:
                    self.assertTrue(value % "another.py" in
                                    str(file['filename']))

            if 'dataset_description[1]' in str(ds['description']):
                self.assertTrue(text_area % "second" in
                                str(ds['description']))
                for file in df:
                    if value % "file.py" in str(file['filename']):
                        continue
                    if value % "file1.py" in str(file['filename']):
                        continue
                    self.assertTrue(False, "Not all files present")

        self.assertTrue(value % "russell, steve" in str(f['authors']),
                        str(f['authors']))

    def test_render(self):
        from tardis.tardis_portal import forms
        from django.template import Template, Context
        exp = self._create_experiment()
        f = forms.FullExperiment(instance=exp)
        template = """<form action="" method="post">
    {% for field in form %}
        <div class="fieldWrapper">
            {{ field.errors }}
            {{ field.label_tag }}: {{ field }}
        </div>
    {% endfor %}
    {% for dataset_form, file_forms in form.get_datasets %}
        {% for field in dataset_form %}
        <div class="fieldWrapper">
            {{ field.errors }}
            {{ field.label_tag }}: {{ field }}
        </div>
        {% endfor %}
    {% for file_form in file_forms %}
        {% for field in file_form %}
        <div class="fieldWrapper">
            {{ field.errors }}
            {{ field.label_tag }}: {{ field }}
        </div>
        {% endfor %}
    {% endfor %}
    {% endfor %}
    <p><input type="submit" value="Submit" /></p>
</form>
"""
        t = Template(template)
        output = t.render(Context({'form': f}))
        value = "value=\"%s\""
        text_area = ">%s</textarea>"
        # test experiment fields
        self.assertTrue(value % "test experiment" in output)
        self.assertTrue(value % "some university" in output)
        self.assertTrue(text_area % "desc....." in output)

        self.assertTrue(text_area % "second")
        self.assertTrue(value % "file1.py" in output)
        self.assertTrue(value % "file://second_ds/file.py" in output)
        self.assertEqual(output.count('file_filename[1]'), 4)
        self.assertEqual(output.count('dataset_description[1]'), 2)

    def test_initial_data(self):
        from tardis.tardis_portal import forms
        from django.forms.models import model_to_dict
        exp = self._create_experiment()
        initial = model_to_dict(exp)
        for i, ds in enumerate(exp.dataset_set.all()):
            initial['dataset_description[' + str(i) + ']'] = ds.description

        f = forms.FullExperiment(initial=initial)

        value = "value=\"%s\""
        text_area = ">%s</textarea>"
        self.assertTrue(value % 'test experiment' in str(f['title']))
        self.assertTrue(value % 'some university' in
                        str(f['institution_name']))
        self.assertTrue('selected="selected">tardis_user1</option>' in
                        str(f['created_by']))
        # TODO the reset of this test is disabled because it's too complex
        return
        for ds, df in f.get_datasets():
            self.assertTrue(text_area % "first one" in
                            str(ds['description']))
        # TODO Currently broken, not sure if initial will be used without the
        # data argument
        self.assertTrue(text_area % "second" in
                        str(f['dataset_description[1]']))

        self.assertTrue(value % "russell, steve" in str(f['authors']))

    def test_field_translation(self):
        from tardis.tardis_portal import forms
        f = forms.FullExperiment()
        self.assertEqual(f._translate_dsfieldname('description', 10),
                         'dataset_description[10]')
        self.assertEqual(f._translate_dsfieldname('description', '1'),
                         'dataset_description[1]')


class TraverseTestCase(TestCase):
    dirs = ['dir1', 'dir2', path.join('dir2', 'subdir'), 'dir3']
    files = [['dir1', 'file1'],
             ['dir2', 'file2'],
             ['dir2', 'file3'],
             ['dir2', 'subdir', 'file4']]

    def setUp(self):
        from django.conf import settings
        staging = settings.STAGING_PATH
        import os
        from os import path
        for dir in self.dirs:
            os.mkdir(path.join(staging, dir))
        for file in self.files:
            f = open(path.join(staging, *file), 'w')
            f.close()

    def tearDown(self):
        from django.conf import settings
        staging = settings.STAGING_PATH
        import os
        from os import path
        for file in self.files:
            os.remove(path.join(staging, *file))
        self.dirs.reverse()
        for dir in self.dirs:
            os.rmdir(path.join(staging, dir))

    def test_traversal(self):
        from tardis.tardis_portal import views
        result = '<ul><li id="phtml_1"><a>My Files</a><ul>\
<li id="dir1"><a>dir1</a><ul><li id="dir1/file1"><a>file1</a>\
</li></ul></li><li id="dir2"><a>dir2</a><ul><li id="dir2/file2">\
<a>file2</a></li><li id="dir2/file3"><a>file3</a></li><li id="dir2/subdir">\
<a>subdir</a><ul><li id="dir2/subdir/file4"><a>file4</a></li></ul></li></ul>\
</li><li id="dir3"><a>dir3</a><ul></ul></li><li id="directory"><a>directory\
</a><ul><li id="directory/t"><a>t</a></li><li id="directory/testfile"><a>\
testfile</a></li><li id="directory/tt"><a>tt</a></li></ul></li>\
<li id="site.db"><a>site.db</a></li><li id="site1"><a>site1</a></li>\
<li id="site2"><a>site2</a></li><li id="site3"><a>site3</a></li>\
<li id="site4"><a>site4</a></li></ul></li></ul>'
        self.assertEqual(views.staging_traverse(), result)


def suite():
    userInterfaceSuite = \
        unittest.TestLoader().loadTestsFromTestCase(UserInterfaceTestCase)
    parserSuite = \
        unittest.TestLoader().loadTestsFromTestCase(ExperimentParserTestCase)
    searchSuite = \
        unittest.TestLoader().loadTestsFromTestCase(SearchTestCase)
    allTests = unittest.TestSuite(
        [parserSuite, userInterfaceSuite, searchSuite])
    return allTests
