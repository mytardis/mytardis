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
test_views.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>

"""
from django.test import TestCase


class UploadTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

    def testFileUpload(self):
        from django.http import QueryDict, HttpRequest
        from tardis.tardis_portal.views import upload
        from django.core.files import File
        from django.core.files.uploadedfile import UploadedFile
        from os import path, mkdir
        from tempfile import mkdtemp
        from shutil import rmtree
        from django.conf import settings
        from django.utils.datastructures import MultiValueDict

        test_dir = mkdtemp()

        from tardis.tardis_portal import models
        exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                created_by=self.user,
                                )
        exp.save()

        dataset = models.Dataset(description="dataset description...",
                                 experiment=exp)
        dataset.save()

        experiment_path = path.join(settings.FILE_STORE_PATH,
                                    str(dataset.experiment.id))

        dataset_path = path.join(experiment_path,
                   str(dataset.id))

        mkdir(experiment_path)
        mkdir(dataset_path)

        #write test file
        filename = "testfile.txt"

        f1 = open(path.join(test_dir, filename), 'w')
        f1.write("Test file 1")
        f1.close()

        f1_size = path.getsize(path.join(test_dir, filename))

        f1 = open(path.join(test_dir, filename), 'r')

        #create request.FILES object
        django_file = File(f1)
        uploaded_file = UploadedFile(file=django_file)
        uploaded_file.name = filename
        uploaded_file.size = f1_size

        post_data = [('enctype', "multipart/form-data")]
        post = QueryDict('&'.join(['%s=%s' % (k, v) for k, v in post_data]))

        files = MultiValueDict({'Filedata': [uploaded_file]})
        request = HttpRequest()
        request.FILES = files
        request.POST = post
        request.method = "POST"
        response = upload(request, dataset.id)

        test_files_db = models.Dataset_File.objects.filter(
            dataset__id=dataset.id)

        self.assertTrue(path.exists(path.join(dataset_path, filename)))
        self.assertTrue(dataset.id == 1)
        self.assertTrue(test_files_db[0].url == "file://1/testfile.txt")

        f1.close()
        rmtree(test_dir)
        rmtree(dataset_path)
        rmtree(experiment_path)
        exp.delete()

    def testUploadComplete(self):
        from django.http import QueryDict, HttpRequest
        from tardis.tardis_portal.views import upload_complete
        data = [('filesUploaded', '1'),
                ('speed', 'really fast!'),
                ('allBytesLoaded', '2'),
                ('errorCount', '0')]
        post = QueryDict('&'.join(['%s=%s' % (k, v) for k, v in data]))
        request = HttpRequest()
        request.POST = post
        response = upload_complete(request)
        self.assertTrue("<p>Number: 1</p>" in response.content)
        self.assertTrue("<p>Errors: 0</p>" in response.content)
        self.assertTrue("<p>Bytes: 2</p>" in response.content)
        self.assertTrue("<p>Speed: really fast!</p>" in response.content)
