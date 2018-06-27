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
test_models.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>

"""
from StringIO import StringIO

from django.conf import settings
from django.test import TestCase
from tastypie.utils import trailing_slash


class ModelTestCase(TestCase):

    def setUp(self):
        from django.contrib.auth.models import User
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

    def test_experiment(self):
        from tardis.tardis_portal import models
        from os import path
        exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                created_by=self.user,
                                )
        exp.save()
        self.assertEqual(exp.title, 'test exp1')
        self.assertEqual(exp.url, None)
        self.assertEqual(exp.institution_name, 'monash')
        self.assertEqual(exp.approved, False)
        self.assertEqual(exp.handle, None)
        self.assertEqual(exp.created_by, self.user)
        self.assertEqual(exp.public_access,
                         models.Experiment.PUBLIC_ACCESS_NONE)
        target_id = models.Experiment.objects.first().id
        self.assertEqual(
            exp.get_absolute_url(), '/experiment/view/%d/' % target_id,
            exp.get_absolute_url() + ' != /experiment/view/%d/' % target_id)
        self.assertEqual(exp.get_or_create_directory(),
                         path.join(settings.FILE_STORE_PATH, str(exp.id)))

    def test_dataset(self):
        from tardis.tardis_portal import models
        exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                created_by=self.user,
                                )

        exp.save()
        exp2 = models.Experiment(title='test exp2',
                                 institution_name='monash',
                                 created_by=self.user,
                                 )
        exp2.save()

        group = models.Group(name="Test Manager Group")
        group.save()
        group.user_set.add(self.user)
        facility = models.Facility(name="Test Facility",
                                   manager_group=group)
        facility.save()
        instrument = models.Instrument(name="Test Instrument",
                                       facility=facility)
        instrument.save()

        dataset = models.Dataset(description='test dataset1')
        dataset.instrument = instrument
        dataset.save()
        dataset.experiments.set([exp, exp2])
        dataset.save()
        dataset_id = dataset.id

        del dataset
        dataset = models.Dataset.objects.get(pk=dataset_id)

        self.assertEqual(dataset.description, 'test dataset1')
        self.assertEqual(dataset.experiments.count(), 2)
        self.assertIn(exp, list(dataset.experiments.iterator()))
        self.assertIn(exp2, list(dataset.experiments.iterator()))
        self.assertEqual(instrument, dataset.instrument)
        target_id = models.Dataset.objects.first().id
        self.assertEqual(
            dataset.get_absolute_url(), '/dataset/%d' % target_id,
            dataset.get_absolute_url() + ' != /dataset/%d' % target_id)

    def test_authors(self):
        from tardis.tardis_portal import models
        exp = models.Experiment(title='test exp2',
                                institution_name='monash',
                                created_by=self.user,
                                )
        exp.save()

        models.ExperimentAuthor(experiment=exp,
                                author='nigel',
                                order=0).save()

        exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                created_by=self.user,
                                )
        exp.save()

        ae1 = models.ExperimentAuthor(experiment=exp,
                                      author='steve',
                                      order=100)
        ae1.save()

        ae2 = models.ExperimentAuthor(experiment=exp,
                                      author='russell',
                                      order=1)
        ae2.save()

        ae3 = models.ExperimentAuthor(experiment=exp,
                                      author='uli',
                                      order=50)
        ae3.save()

        authors = exp.experimentauthor_set.all()

        # confirm that there are 2 authors
        self.assertEqual(len(authors), 3)
        self.assertTrue(ae1 in authors)
        self.assertTrue(ae2 in authors)
        self.assertTrue(ae3 == authors[1])

    def test_datafile(self):
        from tardis.tardis_portal.models import Experiment, Dataset, DataFile

        def _build(dataset, filename, url=None):
            datafile = DataFile(dataset=dataset, filename=filename)
            datafile.save()
            if url is None:
                datafile.file_object = StringIO('bla')
                return datafile
            from tardis.tardis_portal.models import \
                DataFileObject
            dfo = DataFileObject(
                datafile=datafile,
                storage_box=datafile.get_default_storage_box(),
                uri=url)
            dfo.save()
            return datafile

        exp = Experiment(title='test exp1',
                         institution_name='monash',
                         approved=True,
                         created_by=self.user,
                         public_access=Experiment.PUBLIC_ACCESS_NONE)
        exp.save()

        dataset = Dataset(description="dataset description...\nwith; issues")
        dataset.save()
        dataset.experiments.add(exp)
        dataset.save()

        save1 = settings.REQUIRE_DATAFILE_SIZES
        save2 = settings.REQUIRE_DATAFILE_CHECKSUMS
        try:
            settings.REQUIRE_DATAFILE_SIZES = False
            settings.REQUIRE_DATAFILE_CHECKSUMS = False
            df_file = _build(dataset, 'file.txt', 'path/file.txt')
            first_id = df_file.id
            self.assertEqual(df_file.filename, 'file.txt')
            self.assertEqual(df_file.file_objects.all()[0].uri,
                             'path/file.txt')
            self.assertEqual(df_file.dataset, dataset)
            self.assertEqual(df_file.size, None)
            self.assertEqual(df_file.get_download_url(),
                             '/api/v1/dataset_file/%d/download%s' %
                             (first_id, trailing_slash()))

            df_file = _build(dataset, 'file1.txt', 'path/file1.txt')
            self.assertEqual(df_file.filename, 'file1.txt')
            self.assertEqual(df_file.file_objects.all()[0].uri,
                             'path/file1.txt')
            self.assertEqual(df_file.dataset, dataset)
            self.assertEqual(df_file.size, None)
            self.assertEqual(df_file.get_download_url(),
                             '/api/v1/dataset_file/%d/download%s' %
                             (first_id + 1, trailing_slash()))

            df_file = _build(dataset, 'file2.txt', 'path/file2#txt')
            self.assertEqual(df_file.filename, 'file2.txt')
            self.assertEqual(df_file.dataset, dataset)
            self.assertEqual(df_file.size, None)
            self.assertEqual(df_file.get_download_url(),
                             '/api/v1/dataset_file/%d/download%s' %
                             (first_id + 2, trailing_slash()))

            df_file = _build(dataset, 'f.txt',
                             'http://localhost:8080/filestore/f.txt')
            self.assertEqual(df_file.filename, 'f.txt')
            self.assertEqual(df_file.dataset, dataset)
            self.assertEqual(df_file.size, None)
            self.assertEqual(df_file.get_download_url(),
                             '/api/v1/dataset_file/%d/download%s' %
                             (first_id + 3, trailing_slash()))

            df_file = _build(dataset, 'f-bad-ds.txt')
            self.assertEqual(df_file.filename, 'f-bad-ds.txt')
            self.assertEqual(df_file.dataset, dataset)
            self.assertEqual(df_file.size, None)
            self.assertEqual(df_file.get_download_url(),
                             '/api/v1/dataset_file/%d/download%s' %
                             (first_id + 4, trailing_slash()))
            self.assertNotRegexpMatches(df_file.file_objects.first().uri,
                                        '\n|;')

            # check that can't save negative byte sizes
            with self.assertRaises(Exception):
                settings.REQUIRE_DATAFILE_SIZES = True
                DataFile(dataset=dataset, filename='lessthanempty.txt',
                         size=-1).save()

            # Now check the 'REQUIRE' config params
            with self.assertRaises(Exception):
                settings.REQUIRE_DATAFILE_SIZES = True
                settings.REQUIRE_DATAFILE_CHECKSUMS = False
                DataFile(dataset=dataset, filename='foo.txt',
                         md5sum='bad').save()
            with self.assertRaises(Exception):
                settings.REQUIRE_DATAFILE_SIZES = False
                settings.REQUIRE_DATAFILE_CHECKSUMS = True
                DataFile(dataset=dataset, filename='foo.txt',
                         size=1).save()

        finally:
            settings.REQUIRE_DATAFILE_SIZES = save1
            settings.REQUIRE_DATAFILE_CHECKSUMS = save2

    # check conversion of b64encoded images back into files
    def test_parameter(self):
        from tardis.tardis_portal import models
        exp = models.Experiment(
            title='test exp1',
            institution_name='Australian Synchrotron',
            approved=True,
            created_by=self.user,
            public_access=models.Experiment.PUBLIC_ACCESS_NONE,
        )
        exp.save()

        dataset = models.Dataset(description="dataset description")
        dataset.save()
        dataset.experiments.add(exp)
        dataset.save()

        df_file = models.DataFile(dataset=dataset,
                                  filename='file.txt',
                                  size=42,
                                  md5sum='bogus')
        df_file.save()

        df_schema = models.Schema(
            namespace='http://www.cern.ch/felzmann/schema1.xml',
            type=models.Schema.DATAFILE)
        df_schema.save()

        ds_schema = models.Schema(
            namespace='http://www.cern.ch/felzmann/schema2.xml',
            type=models.Schema.DATASET)
        ds_schema.save()

        exp_schema = models.Schema(
            namespace='http://www.cern.ch/felzmann/schema3.xml',
            type=models.Schema.EXPERIMENT)
        exp_schema.save()

        df_parname = models.ParameterName(
            schema=df_schema,
            name='name',
            full_name='full_name',
            units='image/jpg',
            data_type=models.ParameterName.FILENAME)
        df_parname.save()

        ds_parname = models.ParameterName(
            schema=ds_schema,
            name='name',
            full_name='full_name',
            units='image/jpg',
            data_type=models.ParameterName.FILENAME)
        ds_parname.save()

        exp_parname = models.ParameterName(
            schema=exp_schema,
            name='name',
            full_name='full_name',
            units='image/jpg',
            data_type=models.ParameterName.FILENAME)
        exp_parname.save()

        df_parset = models.DatafileParameterSet(schema=df_schema,
                                                datafile=df_file)
        df_parset.save()

        ds_parset = models.DatasetParameterSet(schema=ds_schema,
                                               dataset=dataset)
        ds_parset.save()

        exp_parset = models.ExperimentParameterSet(schema=exp_schema,
                                                   experiment=exp)
        exp_parset.save()

        from os import path
        with self.settings(METADATA_STORE_PATH=path.dirname(__file__)):
            filename = 'test.jpg'
            df_parameter = models.DatafileParameter(name=df_parname,
                                                    parameterset=df_parset,
                                                    string_value=filename)
            df_parameter.save()

            ds_parameter = models.DatasetParameter(name=ds_parname,
                                                   parameterset=ds_parset,
                                                   string_value=filename)
            ds_parameter.save()

            exp_parameter = models.ExperimentParameter(name=exp_parname,
                                                       parameterset=exp_parset,
                                                       string_value=filename)
            exp_parameter.save()

            self.assertEqual(
                "<a href='/display/DatafileImage/load/%i/' target='_blank'><img style='width: 300px;' src='/display/DatafileImage/load/%i/' /></a>" %  # noqa
                (df_parameter.id, df_parameter.id), df_parameter.get())

            self.assertEqual(
                "<a href='/display/DatasetImage/load/%i/' target='_blank'><img style='width: 300px;' src='/display/DatasetImage/load/%i/' /></a>" %  # noqa
                (ds_parameter.id, ds_parameter.id), ds_parameter.get())

            self.assertEqual(
                "<a href='/display/ExperimentImage/load/%i/' target='_blank'><img style='width: 300px;' src='/display/ExperimentImage/load/%i/' /></a>" %   # noqa
                (exp_parameter.id, exp_parameter.id), exp_parameter.get())

    # Verify that create a new user will generate an api_key automtically
    def test_create_user_automatically_generate_api_key(self):
        from django.contrib.auth.models import User
        user = User.objects.create_user('test', 'test@example.com', 'passw0rd')
        user.save()

        try:
            api_key = user.api_key
        except:
            api_key = None

        self.assertIsNotNone(api_key)
