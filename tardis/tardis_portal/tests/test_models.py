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
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
import os
import re
from io import StringIO

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.db import models
from django.test import TestCase
from tastypie.utils import trailing_slash

from ..models import Facility, Instrument

from ..models import Experiment, ExperimentAuthor, ObjectACL

from ..models import Dataset, DataFile, DataFileObject

from ..models import (
    Schema, ParameterName, DatafileParameterSet, DatafileParameter,
    DatasetParameterSet, DatasetParameter, ExperimentParameterSet,
    ExperimentParameter)


class ModelTestCase(TestCase):

    def setUp(self):
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

    def test_experiment(self):
        exp = Experiment(title='test exp1',
                         institution_name='monash',
                         created_by=self.user)
        exp.save()
        self.assertEqual(exp.title, 'test exp1')
        self.assertEqual(exp.url, None)
        self.assertEqual(exp.institution_name, 'monash')
        self.assertEqual(exp.approved, False)
        self.assertEqual(exp.handle, None)
        self.assertEqual(exp.created_by, self.user)
        self.assertEqual(exp.public_access,
                         Experiment.PUBLIC_ACCESS_NONE)
        target_id = Experiment.objects.first().id
        self.assertEqual(
            exp.get_absolute_url(), '/experiment/view/%d/' % target_id,
            exp.get_absolute_url() + ' != /experiment/view/%d/' % target_id)
        self.assertEqual(exp.get_or_create_directory(),
                         os.path.join(settings.FILE_STORE_PATH, str(exp.id)))

    def test_dataset(self):
        exp = Experiment(title='test exp1',
                         institution_name='monash',
                         created_by=self.user)

        exp.save()
        exp2 = Experiment(title='test exp2',
                          institution_name='monash',
                          created_by=self.user)
        exp2.save()

        group = Group(name="Test Manager Group")
        group.save()
        group.user_set.add(self.user)
        facility = Facility(name="Test Facility",
                            manager_group=group)
        facility.save()
        instrument = Instrument(name="Test Instrument",
                                facility=facility)
        instrument.save()

        dataset = Dataset(description='test dataset1')
        dataset.instrument = instrument
        dataset.save()
        dataset.experiments.set([exp, exp2])
        dataset.save()
        dataset_id = dataset.id

        del dataset
        dataset = Dataset.objects.get(pk=dataset_id)

        self.assertEqual(dataset.description, 'test dataset1')
        self.assertEqual(dataset.experiments.count(), 2)
        self.assertIn(exp, list(dataset.experiments.iterator()))
        self.assertIn(exp2, list(dataset.experiments.iterator()))
        self.assertEqual(instrument, dataset.instrument)
        target_id = Dataset.objects.first().id
        self.assertEqual(
            dataset.get_absolute_url(), '/dataset/%d' % target_id,
            dataset.get_absolute_url() + ' != /dataset/%d' % target_id)

    def test_authors(self):
        exp = Experiment(title='test exp2',
                         institution_name='monash',
                         created_by=self.user,
                         )
        exp.save()

        ExperimentAuthor(experiment=exp,
                         author='nigel',
                         order=0).save()

        exp = Experiment(title='test exp1',
                         institution_name='monash',
                         created_by=self.user,
                         )
        exp.save()

        ae1 = ExperimentAuthor(experiment=exp,
                               author='steve',
                               order=100)
        ae1.save()

        ae2 = ExperimentAuthor(experiment=exp,
                               author='russell',
                               order=1)
        ae2.save()

        ae3 = ExperimentAuthor(experiment=exp,
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

        def _build(dataset, filename, url=None):
            datafile = DataFile(dataset=dataset, filename=filename)
            datafile.save()
            if url is None:
                datafile.file_object = StringIO(u'bla')
                return datafile
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

        acl = ObjectACL(
            pluginId='django_user',
            entityId=str(self.user.id),
            content_object=exp,
            canRead=True,
            canWrite=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED,
        )
        acl.save()

        dataset = Dataset(description="dataset description...\nwith; issues")
        dataset.save()
        dataset.experiments.add(exp)
        dataset.save()

        save1 = settings.REQUIRE_DATAFILE_SIZES
        save2 = settings.REQUIRE_DATAFILE_CHECKSUMS
        saved_render_image_size_limit = getattr(
            settings, 'RENDER_IMAGE_SIZE_LIMIT', 0)
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
            self.assertEqual(df_file.download_url,
                             '/api/v1/dataset_file/%d/download%s' %
                             (first_id, trailing_slash()))

            # Test string representation of DataFileObject:
            dfo = df_file.get_preferred_dfo()
            self.assertEqual(
                str(dfo),
                "Box: %s, URI: %s, verified: %s"
                % (str(dfo.storage_box), dfo.uri, str(dfo.verified)))

            # Test constructing absolute file path:
            self.assertEqual(
                df_file.get_absolute_filepath(),
                os.path.join(settings.DEFAULT_STORAGE_BASE_DIR, dfo.uri))

            # get_as_temporary_file() doesn't work for a StringIO file object:
            with open (dfo.get_full_path(), 'w') as file_obj:
                file_obj.write(u'bla')
            # Test ability to check out a temporary copy of file:
            with df_file.get_as_temporary_file() as temp_file_obj:
                self.assertEqual(temp_file_obj.read().decode(), u'bla')

            self.assertFalse(df_file.has_image)
            # Test checking online status, i.e. whether the DataFile
            # has at least one verified DataFileObject in a non-tape
            # storage box:
            self.assertTrue(df_file.is_online)
            DataFileObject.objects.get(datafile=df_file).delete()
            # This behaviour is documented in the is_online property
            # method's docstring, i.e. is_online is expected to be
            # True for a DataFile without any DataFileObjects:
            self.assertTrue(df_file.is_online)

            # Test method for getting MIME type:
            self.assertEqual(df_file.get_mimetype(), "text/plain")
            df_file.mimetype = ""
            # DataFile's save automatically updates the mimetype,
            # and we want to test get_mimetype without a mimetype:
            models.Model.save(df_file)
            self.assertEqual(df_file.get_mimetype(), "text/plain")
            df_file.filename = "file.unknown-extension"
            models.Model.save(df_file)
            self.assertEqual(
                df_file.get_mimetype(), "application/octet-stream")

            # Test method for getting view URL for file types which can
            # be displayed in the browser.
            # First test a file of unknown MIME type:
            self.assertIsNone(df_file.view_url)
            # Now test for a text/plain file:
            df_file.filename = "file.txt"
            df_file.save()
            # Clear cache for view_url @cached_property by creating new instance:
            df_file = DataFile.objects.get(id=df_file.id)
            self.assertEqual(df_file.mimetype, "text/plain")
            self.assertEqual(
                df_file.view_url, "/datafile/view/%s/" % df_file.id)
            # This setting will prevent files larger than 2 bytes
            # from being rendered in the browser:
            settings.RENDER_IMAGE_SIZE_LIMIT = 2
            df_file.size = 3
            df_file.save()
            # Clear cache for view_url @cached_property by creating new instance:
            df_file = DataFile.objects.get(id=df_file.id)
            self.assertIsNone(df_file.view_url)

            df_file = _build(dataset, 'file1.txt', 'path/file1.txt')
            self.assertEqual(df_file.filename, 'file1.txt')
            self.assertEqual(df_file.file_objects.all()[0].uri,
                             'path/file1.txt')
            self.assertEqual(df_file.dataset, dataset)
            self.assertEqual(df_file.size, None)
            self.assertEqual(df_file.download_url,
                             '/api/v1/dataset_file/%d/download%s' %
                             (first_id + 1, trailing_slash()))

            df_file = _build(dataset, 'file2.txt', 'path/file2#txt')
            self.assertEqual(df_file.filename, 'file2.txt')
            self.assertEqual(df_file.dataset, dataset)
            self.assertEqual(df_file.size, None)
            self.assertEqual(df_file.download_url,
                             '/api/v1/dataset_file/%d/download%s' %
                             (first_id + 2, trailing_slash()))

            df_file = _build(dataset, 'f.txt',
                             'http://localhost:8080/filestore/f.txt')
            self.assertEqual(df_file.filename, 'f.txt')
            self.assertEqual(df_file.dataset, dataset)
            self.assertEqual(df_file.size, None)
            self.assertEqual(df_file.download_url,
                             '/api/v1/dataset_file/%d/download%s' %
                             (first_id + 3, trailing_slash()))

            df_file = _build(dataset, 'f-bad-ds.txt')
            self.assertEqual(df_file.filename, 'f-bad-ds.txt')
            self.assertEqual(df_file.dataset, dataset)
            self.assertEqual(df_file.size, None)
            self.assertEqual(df_file.download_url,
                             '/api/v1/dataset_file/%d/download%s' %
                             (first_id + 4, trailing_slash()))
            pattern = re.compile( '\n|;')
            self.assertFalse(pattern.search(df_file.file_objects.first().uri))

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
            settings.RENDER_IMAGE_SIZE_LIMIT = saved_render_image_size_limit

    def test_deleting_dfo_without_uri(self):
        dataset = Dataset(description="dataset description")
        dataset.save()
        save1 = settings.REQUIRE_DATAFILE_SIZES
        save2 = settings.REQUIRE_DATAFILE_CHECKSUMS
        try:
            settings.REQUIRE_DATAFILE_SIZES = False
            settings.REQUIRE_DATAFILE_CHECKSUMS = False
            datafile = DataFile(dataset=dataset, filename='test1.txt')
            datafile.save()
        finally:
            settings.REQUIRE_DATAFILE_SIZES = save1
            settings.REQUIRE_DATAFILE_CHECKSUMS = save2
        dfo = DataFileObject(
                datafile=datafile,
                storage_box=datafile.get_default_storage_box(),
                uri=None)
        dfo.save()
        self.assertIsNone(dfo.uri)
        self.assertIsNotNone(dfo.id)
        dfo.delete()
        self.assertIsNone(dfo.id)

    # check conversion of b64encoded images back into files
    def test_parameter(self):
        exp = Experiment(
            title='test exp1',
            institution_name='Australian Synchrotron',
            approved=True,
            created_by=self.user,
            public_access=Experiment.PUBLIC_ACCESS_NONE,
        )
        exp.save()

        dataset = Dataset(description="dataset description")
        dataset.save()
        dataset.experiments.add(exp)
        dataset.save()

        df_file = DataFile(dataset=dataset,
                           filename='file.txt',
                           size=42,
                           md5sum='bogus')
        df_file.save()

        df_schema = Schema(
            namespace='http://www.cern.ch/felzmann/schema1.xml',
            type=Schema.DATAFILE)
        df_schema.save()

        ds_schema = Schema(
            namespace='http://www.cern.ch/felzmann/schema2.xml',
            type=Schema.DATASET)
        ds_schema.save()

        exp_schema = Schema(
            namespace='http://www.cern.ch/felzmann/schema3.xml',
            type=Schema.EXPERIMENT)
        exp_schema.save()

        df_parname = ParameterName(
            schema=df_schema,
            name='name',
            full_name='full_name',
            units='image/jpg',
            data_type=ParameterName.FILENAME)
        df_parname.save()

        ds_parname = ParameterName(
            schema=ds_schema,
            name='name',
            full_name='full_name',
            units='image/jpg',
            data_type=ParameterName.FILENAME)
        ds_parname.save()

        exp_parname = ParameterName(
            schema=exp_schema,
            name='name',
            full_name='full_name',
            units='image/jpg',
            data_type=ParameterName.FILENAME)
        exp_parname.save()

        df_parset = DatafileParameterSet(schema=df_schema,
                                         datafile=df_file)
        df_parset.save()

        ds_parset = DatasetParameterSet(schema=ds_schema,
                                        dataset=dataset)
        ds_parset.save()

        exp_parset = ExperimentParameterSet(schema=exp_schema,
                                            experiment=exp)
        exp_parset.save()

        with self.settings(METADATA_STORE_PATH=os.path.dirname(__file__)):
            filename = 'test.jpg'
            df_parameter = DatafileParameter(name=df_parname,
                                             parameterset=df_parset,
                                             string_value=filename)
            df_parameter.save()

            ds_parameter = DatasetParameter(name=ds_parname,
                                            parameterset=ds_parset,
                                            string_value=filename)
            ds_parameter.save()

            exp_parameter = ExperimentParameter(name=exp_parname,
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
        user = User.objects.create_user('test', 'test@example.com', 'passw0rd')
        user.save()

        try:
            api_key = user.api_key
        except:
            api_key = None

        self.assertIsNotNone(api_key)
