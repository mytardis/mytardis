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
from django.test import TestCase
from nose.plugins.skip import SkipTest


class ExperimentFormTestCase(TestCase):

    def setUp(self):
        from django.contrib.auth.models import User
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)
        # skipping create_experiment tests until they reflect new code
        raise SkipTest()

    def _data_to_post(self, data=None):
        from django.http import QueryDict
        data = data or [('authors', 'russell, steve'),
                        ('created_by', self.user.pk),
                        ('description', 'desc.....'),
                        ('institution_name', 'some university'),
                        ('title', 'test experiment'),
                        ('url', 'http://www.test.com'),
                        ('dataset-MAX_NUM_FORMS', ''),
                        ('dataset-INITIAL_FORMS', '0'),
                        ('dataset-TOTAL_FORMS', '2'),
                        ('dataset-0-datafile-MAX_NUM_FORMS', ''),
                        ('dataset-0-datafile-INITIAL_FORMS', '0'),
                        ('dataset-0-datafile-TOTAL_FORMS', '1'),
                        ('dataset-0-id', ''),
                        ('dataset-0-description', 'first one'),
                        ('dataset-0-datafile-0-filename', 'file/another.py'),
                        ('dataset-1-description', 'second'),
                        ('dataset-1-datafile-MAX_NUM_FORMS', ''),
                        ('dataset-1-datafile-INITIAL_FORMS', '0'),
                        ('dataset-1-datafile-TOTAL_FORMS', '2'),
                        ('dataset-1-datafile-0-id', ''),
                        ('dataset-1-datafile-0-filename', 'second_ds/file.py'),
                        ('dataset-1-datafile-1-id', ''),
                        ('dataset-1-datafile-1-filename', 'second_ds/file1.py'),
                        ]
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
            ae = models.Author_Experiment(experiment=exp,
                                          author=a,
                                          order=i)
            ae.save()
        ds_desc = {'first one': ['file/another.py'],
                   'second': ['second_ds/file.py', 'second_ds/file1.py']}
        for d, df in ds_desc.items():
            dataset = models.Dataset(description=d,
                                     experiment=exp)
            dataset.save()
            for f in df:
                d = models.Dataset_File(url='file://' + f,
                                         dataset=dataset,
                                         filename=basename(f))
                d.save()
        return exp

    def test_form_printing(self):
        from tardis.tardis_portal import forms

        example_post = self._data_to_post()

        f = forms.ExperimentForm(example_post)
        as_table = """<tr><th><label for="url">Url:</label></th><td><input type="text" name="url" value="http://www.test.com" id="url" /></td></tr>
<tr><th><label for="title">Title:</label></th><td><input id="title" type="text" name="title" value="test experiment" maxlength="400" /></td></tr>
<tr><th><label for="institution_name">Institution name:</label></th><td><input id="institution_name" type="text" name="institution_name" value="some university" maxlength="400" /></td></tr>
<tr><th><label for="description">Description:</label></th><td><textarea id="description" rows="10" cols="40" name="description">desc.....</textarea></td></tr>
<tr><th><label for="start_time">Start time:</label></th><td><input type="text" name="start_time" id="start_time" /></td></tr>
<tr><th><label for="end_time">End time:</label></th><td><input type="text" name="end_time" id="end_time" /></td></tr>
<tr><th><label for="public">Public:</label></th><td><input type="checkbox" name="public" id="public" /></td></tr>
<tr><th><label for="authors">Authors:</label></th><td><input type="text" name="authors" value="russell, steve" id="authors" /></td></tr>"""
        self.assertEqual(f.as_table(), as_table)

    def test_form_parsing(self):
        from os.path import basename
        from tardis.tardis_portal import forms, models

        example_post = [('title', 'test experiment'),
                        ('url', 'http://www.test.com'),
                        ('institution_name', 'some university'),
                        ('description', 'desc.....'),
                        ('authors', 'russell, steve'),
                        ('dataset-MAX_NUM_FORMS', ''),
                        ('dataset-INITIAL_FORMS', '0'),
                        ('dataset-TOTAL_FORMS', '2'),
                        ('dataset-0-datafile-MAX_NUM_FORMS', ''),
                        ('dataset-0-datafile-INITIAL_FORMS', '0'),
                        ('dataset-0-datafile-TOTAL_FORMS', '2'),
                        ('dataset-0-description', 'first one'),
                        ('dataset-0-id', ''),
                        ('dataset-0-datafile-0-id', ''),
                        ('dataset-0-datafile-0-filename', 'location.py'),
                        ('dataset-0-datafile-0-protocol', ''),
                        ('dataset-0-datafile-0-url', 'file/location.py'),
                        ('dataset-0-datafile-1-id', ''),
                        ('dataset-0-datafile-1-filename', 'another.py'),
                        ('dataset-0-datafile-1-protocol', ''),
                        ('dataset-0-datafile-1-url', 'file/another.py'),
                        ('dataset-1-id', ''),
                        ('dataset-1-description', 'second'),
                        ('dataset-1-datafile-MAX_NUM_FORMS', ''),
                        ('dataset-1-datafile-INITIAL_FORMS', '0'),
                        ('dataset-1-datafile-TOTAL_FORMS', '1'),
                        ('dataset-1-datafile-0-id', ''),
                        ('dataset-1-datafile-0-filename', 'file.py'),
                        ('dataset-1-datafile-0-protocol', ''),
                        ('dataset-1-datafile-0-url', 'second_ds/file.py'),
                        ]
        example_post = self._data_to_post(example_post)

        f = forms.ExperimentForm(example_post)

        # test validity of form data
        self.assertTrue(f.is_valid(), repr(f.errors))

        # save form
        exp = f.save(commit=False)
        exp['experiment'].created_by = self.user
        exp.save_m2m()

        # retrieve model from database
        e = models.Experiment.objects.get(pk=exp['experiment'].pk)
        self.assertEqual(e.title, example_post['title'])
        self.assertEqual(e.institution_name, example_post['institution_name'])
        self.assertEqual(e.description, example_post['description'])

        # test there are 2 authors
        self.assertEqual(len(e.author_experiment_set.all()), 2)

        # check we can get one of the authors back
        self.assertEqual(e.author_experiment_set.get(author='steve').author,
                         'steve')

        # check both datasets have been saved
        ds = models.Dataset.objects.filter(experiment=exp['experiment'].pk)
        self.assertEqual(len(ds), 2)

        # check that all the files exist in the database
        check_files = {'first one': ['file/location.py', 'file/another.py'],
                       'second': ['second_ds/file.py']}
        for d in ds:
            files = models.Dataset_File.objects.filter(dataset=d.pk)
            v_files = [basename(f) for f in check_files[d.description]]
            v_urls = check_files[d.description]
            for f in files:
                self.assertTrue(f.filename in v_files,
                                "%s not in %s" % (f.filename, v_files))
                self.assertTrue(f.url in v_urls,
                                "%s not in %s" % (f.url, v_urls))

    def test_initial_form(self):
        from tardis.tardis_portal import forms

        as_table = """<tr><th><label for="url">Url:</label></th><td><input type="text" name="url" id="url" /></td></tr>
<tr><th><label for="title">Title:</label></th><td><input id="title" type="text" name="title" maxlength="400" /></td></tr>
<tr><th><label for="institution_name">Institution name:</label></th><td><input id="institution_name" type="text" name="institution_name" maxlength="400" /></td></tr>
<tr><th><label for="description">Description:</label></th><td><textarea id="description" rows="10" cols="40" name="description"></textarea></td></tr>
<tr><th><label for="start_time">Start time:</label></th><td><input type="text" name="start_time" id="start_time" /></td></tr>
<tr><th><label for="end_time">End time:</label></th><td><input type="text" name="end_time" id="end_time" /></td></tr>
<tr><th><label for="public">Public:</label></th><td><input type="checkbox" name="public" id="public" /></td></tr>
<tr><th><label for="authors">Authors:</label></th><td><input type="text" name="authors" id="authors" /></td></tr>"""

        f = forms.ExperimentForm()
        self.assertEqual(f.as_table(), as_table)
        #TODO needs to be extended to cover printing initial datasets

    def test_validation(self):
        from tardis.tardis_portal import forms

        # test empty form
        f = forms.ExperimentForm()
        self.assertTrue(f.is_valid())

        # test blank post data
        post = self._data_to_post([('authors', ''),
                                   ('created_by', ''),
                                   ('description', ''),
                                   ('institution_name', ''),
                                   ('title', ''),
                                   ('url', ''),
                                   ('dataset-MAX_NUM_FORMS', ''),
                                   ('dataset-INITIAL_FORMS', '0'),
                                   ('dataset-TOTAL_FORMS', '1'),
                                   ('dataset-0-datafile-MAX_NUM_FORMS', ''),
                                   ('dataset-0-datafile-INITIAL_FORMS', '0'),
                                   ('dataset-0-datafile-TOTAL_FORMS', '1'),
                                   ('dataset-0-id', ''),
                                   ('dataset-0-description', ''),
                                   ])
        f = forms.ExperimentForm(data=post)
        self.assertFalse(f.is_valid())

        # test a valid form
        example_post = self._data_to_post()
        f = forms.ExperimentForm(example_post)
        self.assertTrue(f.is_valid())

        # test a valid instance of a form
        exp = self._create_experiment()
        f = forms.ExperimentForm(instance=exp)
        self.assertTrue(f.is_valid())

        # test a valid instance with unmodified post
        #f = forms.ExperimentForm(instance=exp, data=example_post)
        #self.assertFalse(f.is_valid())

    def test_instance(self):
        from tardis.tardis_portal import forms
        exp = self._create_experiment()
        f = forms.ExperimentForm(instance=exp)
        value = "value=\"%s\""
        text_area = ">%s</textarea>"
        self.assertTrue(value % 'test experiment' in
                        str(f['title']), str(f['title']))
        self.assertTrue(value % 'some university' in
                        str(f['institution_name']))
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
        f = forms.ExperimentForm(instance=exp)
        template = """<form action="" method="post">
    {% for field in form %}
        <div class="fieldWrapper">
            {{ field.errors }}
            {{ field.label_tag }}: {{ field }}
        </div>
    {% endfor %}
    {{ form.datasets.management_form }}
    {% for dataset_form, file_forms in form.get_datasets %}
        {% for field in dataset_form %}
        <div class="fieldWrapper">
            {{ field.errors }}
            {{ field.label_tag }}: {{ field }}
        </div>
        {% endfor %}
    {{ file_forms.management_form }}
    {% for file_form in file_forms.forms %}
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
        span = ">%s</span>"
        text_area = ">%s</textarea>"
        # test experiment fields
        self.assertTrue(value % "test experiment" in output)
        self.assertTrue(value % "some university" in output)
        self.assertTrue(text_area % "desc....." in output)

        self.assertTrue(text_area % "second" in output, output)
        self.assertTrue(span % "file1.py" in output)
        self.assertTrue(value % "file://second_ds/file.py" in output)

        self.assertEqual(output.count('0-datafile-0-url" value'), 1)
        self.assertEqual(output.count('0-datafile-1-url" value'), 1)
        self.assertEqual(output.count('1-datafile-0-url" value'), 1)
        self.assertEqual(output.count('description">first one</text'), 1)
        self.assertEqual(output.count('description">second</text'), 1)

    def test_initial_data(self):
        from tardis.tardis_portal import forms
        from django.forms.models import model_to_dict
        exp = self._create_experiment()
        initial = model_to_dict(exp)
        for i, ds in enumerate(exp.dataset_set.all()):
            initial['dataset_description[' + str(i) + ']'] = ds.description

        f = forms.ExperimentForm(initial=initial)

        value = "value=\"%s\""
        text_area = ">%s</textarea>"
        self.assertTrue(value % 'test experiment' in str(f['title']))
        self.assertTrue(value % 'some university' in
                        str(f['institution_name']))
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
