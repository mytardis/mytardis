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
from django.conf import settings
from django.test import TestCase


class ModelTestCase(TestCase):

    urls = 'tardis.tardis_portal.tests.urls'

    def setUp(self):
        from django.contrib.auth.models import User
        from tardis.tardis_portal.models import Location
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)
        Location.force_initialize()

    def test_experiment(self):
        from tardis.tardis_portal import models
        from django.conf import settings
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
        self.assertEqual(exp.public_access, models.Experiment.PUBLIC_ACCESS_NONE)
        self.assertEqual(exp.get_absolute_url(), '/test/experiment/view/1/',
                         exp.get_absolute_url() + ' != /test/experiment/view/1/')
        self.assertEqual(exp.get_or_create_directory(),
                         path.join(settings.FILE_STORE_PATH, str(exp.id)))

    def test_authors(self):
        from tardis.tardis_portal import models
        exp = models.Experiment(title='test exp2',
                                institution_name='monash',
                                created_by=self.user,
                                )
        exp.save()

        models.Author_Experiment(experiment=exp,
                                 author='nigel',
                                 order=0).save()

        exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                created_by=self.user,
                                )
        exp.save()

        ae1 = models.Author_Experiment(experiment=exp,
                                       author='steve',
                                       order=100)
        ae1.save()

        ae2 = models.Author_Experiment(experiment=exp,
                                       author='russell',
                                       order=1)
        ae2.save()

        ae3 = models.Author_Experiment(experiment=exp,
                                       author='uli',
                                       order=50)
        ae3.save()

        authors = exp.author_experiment_set.all()

        # confirm that there are 2 authors
        self.assertEqual(len(authors), 3)
        self.assertTrue(ae1 in authors)
        self.assertTrue(ae2 in authors)
        self.assertTrue(ae3 == authors[1])

    def test_datafile(self):
        from tardis.tardis_portal.models import Experiment, Dataset

        def _build(dataset, filename, url, protocol):
            from tardis.tardis_portal.models import \
                Dataset_File, Replica, Location
            datafile = Dataset_File(dataset=dataset, filename=filename)
            datafile.save()
            replica = Replica(datafile=datafile, url=url, 
                              protocol=protocol,
                              location=Location.get_default_location())
            replica.save()
            return datafile

        exp = Experiment(title='test exp1',
                         institution_name='monash',
                         approved=True,
                         created_by=self.user,
                         public_access=Experiment.PUBLIC_ACCESS_NONE)
        exp.save()

        dataset = Dataset(description="dataset description...")
        dataset.save()
        dataset.experiments.add(exp)
        dataset.save()

        save1 = settings.REQUIRE_DATAFILE_SIZES
        save2 = settings.REQUIRE_DATAFILE_CHECKSUMS
        try:
            settings.REQUIRE_DATAFILE_SIZES = False
            settings.REQUIRE_DATAFILE_CHECKSUMS = False
            df_file = _build(dataset, 'file.txt', 'path/file.txt', '')
            self.assertEqual(df_file.filename, 'file.txt')
            self.assertEqual(df_file.get_preferred_replica().url, 
                             'path/file.txt')
            self.assertEqual(df_file.get_preferred_replica().protocol, '')
            self.assertEqual(df_file.dataset, dataset)
            self.assertEqual(df_file.size, '')
            self.assertEqual(df_file.get_download_url(), 
                             '/test/download/datafile/1/')
            self.assertTrue(df_file.is_local())
            
            df_file = _build(dataset, 'file1.txt', 'path/file1.txt', 'vbl')
            self.assertEqual(df_file.filename, 'file1.txt')
            self.assertEqual(df_file.get_preferred_replica().url,
                             'path/file1.txt')
            self.assertEqual(df_file.get_preferred_replica().protocol, 'vbl')
            self.assertEqual(df_file.dataset, dataset)
            self.assertEqual(df_file.size, '')
            self.assertEqual(df_file.get_download_url(),
                             '/test/vbl/download/datafile/2/')
            self.assertFalse(df_file.is_local())
            
            df_file = _build(dataset, 'f.txt',
                             'http://localhost:8080/filestore/f.txt', '')
            self.assertEqual(df_file.filename, 'f.txt')
            self.assertEqual(df_file.get_preferred_replica().url,
                             'http://localhost:8080/filestore/f.txt')
            self.assertEqual(df_file.get_preferred_replica().protocol, '')
            self.assertEqual(df_file.dataset, dataset)
            self.assertEqual(df_file.size, '')
            self.assertEqual(df_file.get_download_url(),
                             '/test/download/datafile/3/')
            self.assertFalse(df_file.is_local())
            # Now check the 'REQUIRE' config params
            with self.assertRaises(Exception):
                settings.REQUIRE_DATAFILE_SIZES = True
                settings.REQUIRE_DATAFILE_CHECKSUMS = False
                Dataset_File(dataset=dataset, filename='foo.txt', md5sum='bad')
            with self.assertRaises(Exception):
                settings.REQUIRE_DATAFILE_SIZES = False
                settings.REQUIRE_DATAFILE_CHECKSUMS = True
                Dataset_File(dataset=dataset, filename='foo.txt', size='1')
                
        finally:
            settings.REQUIRE_DATAFILE_SIZES = save1
            settings.REQUIRE_DATAFILE_CHECKSUMS = save2
            

    def test_location(self):
        from tardis.tardis_portal.models import Location
        self.assertEquals(Location.get_default_location().name,
                          'local')
        self.assertEquals(Location.get_location('staging').name,
                          'staging')
        self.assertEquals(len(Location.objects.all()), 6)

    # check conversion of b64encoded images back into files
    def test_parameter(self):
        from tardis.tardis_portal import models
        exp = models.Experiment(title='test exp1',
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

        df_file = models.Dataset_File(dataset=dataset,
                                      filename='file.txt',
                                      size='42',
                                      md5sum='bogus')
        df_file.save()

        df_schema = models.Schema(namespace='http://www.cern.ch/felzmann/schema1.xml',
                                  type=models.Schema.DATAFILE)
        df_schema.save()

        ds_schema = models.Schema(namespace='http://www.cern.ch/felzmann/schema2.xml',
                                  type=models.Schema.DATASET)
        ds_schema.save()

        exp_schema = models.Schema(namespace='http://www.cern.ch/felzmann/schema3.xml',
                                   type=models.Schema.EXPERIMENT)
        exp_schema.save()

        df_parname = models.ParameterName(schema=df_schema,
                                          name='name',
                                          full_name='full_name',
                                          units='image/jpg',
                                          data_type=models.ParameterName.FILENAME)
        df_parname.save()

        ds_parname = models.ParameterName(schema=ds_schema,
                                          name='name',
                                          full_name='full_name',
                                          units='image/jpg',
                                          data_type=models.ParameterName.FILENAME)
        ds_parname.save()

        exp_parname = models.ParameterName(schema=exp_schema,
                                          name='name',
                                          full_name='full_name',
                                          units='image/jpg',
                                          data_type=models.ParameterName.FILENAME)
        exp_parname.save()

        df_parset = models.DatafileParameterSet(schema=df_schema,
                                                dataset_file=df_file)
        df_parset.save()

        ds_parset = models.DatasetParameterSet(schema=ds_schema,
                                               dataset=dataset)
        ds_parset.save()

        exp_parset = models.ExperimentParameterSet(schema=exp_schema,
                                                   experiment=exp)
        exp_parset.save()

        from base64 import b64encode
        from os import path
        from os import remove

        filename = path.join(path.dirname(__file__), 'test.jpg')
        df_parameter = models.DatafileParameter(name=df_parname,
                                                parameterset=df_parset,
                                                string_value=b64encode(open(filename).read()))
        df_parameter.save()

        ds_parameter = models.DatasetParameter(name=ds_parname,
                                               parameterset=ds_parset,
                                               string_value=b64encode(open(filename).read()))
        ds_parameter.save()

        exp_parameter = models.ExperimentParameter(name=exp_parname,
                                                   parameterset=exp_parset,
                                                   string_value=b64encode(open(filename).read()))
        exp_parameter.save()

        self.assertEqual("<a href='/test/DatafileImage/load/%i/' target='_blank'><img style='width: 300px;' src='/test/DatafileImage/load/%i/' /></a>" % (df_parameter.id, df_parameter.id),
                         df_parameter.get())

        self.assertEqual("<a href='/test/DatasetImage/load/%i/' target='_blank'><img style='width: 300px;' src='/test/DatasetImage/load/%i/' /></a>" % (ds_parameter.id, ds_parameter.id),
                         ds_parameter.get())

        self.assertEqual("<a href='/test/ExperimentImage/load/%i/' target='_blank'><img style='width: 300px;' src='/test/ExperimentImage/load/%i/' /></a>" % (exp_parameter.id, exp_parameter.id),
                         exp_parameter.get())

        remove(path.join(settings.FILE_STORE_PATH, df_parameter.string_value))
        remove(path.join(settings.FILE_STORE_PATH, ds_parameter.string_value))
        remove(path.join(settings.FILE_STORE_PATH, exp_parameter.string_value))
