# -*- coding: utf-8 -*-
"""
test_datafile.py

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
import os
import re
from io import StringIO

from unittest.mock import patch

from django.conf import settings
from django.db import models
from django.test import override_settings
from tastypie.utils import trailing_slash

from tardis.tardis_portal.models import Experiment, ObjectACL

from tardis.tardis_portal.models import Dataset, DataFile, DataFileObject

from . import ModelTestCase


class DataFileTestCase(ModelTestCase):

    @override_settings(USE_FILTERS=True)
    @patch('celery.app.base.Celery.send_task')
    def test_datafile(self, mock_send_task):

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
            # Tests are run with task_always_eager = True,
            # so saving a DFO will trigger an immediate attempt
            # to verify the DFO which will trigger an attempt
            # to apply filters because we are overriding the
            # USE_FILTERS setting to True in this test:
            self.assertNotEqual(mock_send_task.call_count, 0)
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
            if not os.path.exists(os.path.dirname(dfo.get_full_path())):
                os.makedirs(os.path.dirname(dfo.get_full_path()))
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
