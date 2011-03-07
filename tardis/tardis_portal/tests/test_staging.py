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
test_views.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>

"""
from os import path

from django.test import TestCase


class StagingFiles(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

    def testDuplicateFileCheckRename(self):
        from os import path
        from tempfile import mkdtemp
        from shutil import rmtree
        from tardis.tardis_portal.staging import duplicate_file_check_rename
        test_dir = mkdtemp()
        path.join(test_dir, "testfile.txt")
        f1 = open(path.join(test_dir, "testfile.txt"), 'w')
        f1.close()
        self.assertEqual(
            path.basename(duplicate_file_check_rename(
                path.join(test_dir, "testfile.txt"))),
            'testfile_1.txt')
        f1 = open(path.join(test_dir, "testfile_1.txt"), 'w')
        f1.close()
        self.assertEqual(
            path.basename(duplicate_file_check_rename(
                path.join(test_dir, "testfile.txt"))),
            'testfile_2.txt')
        rmtree(test_dir)

    def testAddDatafileToDataset(self):
        from tardis.tardis_portal import models
        exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                created_by=self.user,
                                )
        exp.save()
        dataset = models.Dataset(description="dataset description...",
                                 experiment=exp)
        dataset.save()
        from tardis.tardis_portal.staging import add_datafile_to_dataset
        from django.conf import settings
        from os import path
        experiment_path = path.join(settings.FILE_STORE_PATH,
                                    str(dataset.experiment.id))
        df = add_datafile_to_dataset(dataset,
                                     path.join(experiment_path,
                                               str(dataset.id), 'file'),
                                     1234)
        self.assertEqual(df.size, 1234)
        self.assertEqual(df.filename, 'file')
        self.assertEqual(df.url, "file://%s/file" % dataset.id)


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
        from tardis.tardis_portal.staging import staging_traverse
        result = staging_traverse()
        self.assertTrue('dir1' in result)
        self.assertTrue('dir1/file1' in result)
        self.assertTrue('dir2' in result)
        self.assertTrue('dir2/file2' in result)
        self.assertTrue('dir2/file3' in result)
        self.assertTrue('dir2/subdir/file4' in result)
        self.assertTrue('dir3' in result)


class TestPathResolution(TestCase):
    paths = ["dir123/file123",
             "file.txt"]

    def test_absolute_to_relative(self):
        from tardis.tardis_portal import staging
        from django.conf import settings
        from os import path
        for p in self.paths:
            ap = path.join(settings.STAGING_PATH,
                            p)
            self.assertRaises(ValueError,
                              staging.calculate_relative_path,
                              'staging', p)
            sp = staging.calculate_relative_path('staging',
                                               ap)
            self.assertEqual(sp, p)

        for p in self.paths:
            ap = path.join(settings.FILE_STORE_PATH,
                            p)
            self.assertRaises(ValueError,
                              staging.calculate_relative_path,
                              'tardis', p)
            sp = staging.calculate_relative_path('tardis',
                                               ap)
            self.assertEqual(sp, p)


class TestStagingFiles(TestCase):
    def setUp(self):
        from tardis.tardis_portal import models
        from tardis.tardis_portal.staging import calculate_relative_path
        from tempfile import mkdtemp, mktemp
        from django.conf import settings
        from os import path

        # Disconnect post_save signal
        from django.db.models.signals import post_save
        from tardis.tardis_portal.models import staging_hook, Dataset_File
        post_save.disconnect(staging_hook, sender=Dataset_File)

        from django.contrib.auth.models import User
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

        self.temp = mkdtemp(dir=settings.STAGING_PATH)

        self.file = mktemp(dir=self.temp)
        f = open(self.file, "w+b")
        f.write('test file')
        f.close()

        # make datafile
        exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                created_by=self.user,
                                )
        exp.save()

        # make dataset
        dataset = models.Dataset(description="dataset description...",
                                 experiment=exp)
        dataset.save()

        # create datasetfile
        df = models.Dataset_File()
        df.dataset = dataset
        df.filename = path.basename(self.file)
        df.url = self.file
        df.protocol = "staging"
        df.save()
        self.df = df

    def tearDown(self):
        # reconnect post_save signal
        from django.db.models.signals import post_save
        from tardis.tardis_portal.models import staging_hook, Dataset_File
        post_save.connect(staging_hook, sender=Dataset_File)

        from shutil import rmtree
        rmtree(self.temp)

    def test_stage_file(self):
        from tardis.tardis_portal import staging

        staging.stage_file(self.df)
