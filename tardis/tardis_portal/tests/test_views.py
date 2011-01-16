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
test_views.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>

"""
from django.test import TestCase


class StagingFiles(TestCase):
    def testDuplicateFileCheckRename(self):
        from os import path
        from tempfile import mkdtemp
        from shutil import rmtree
        from tardis.tardis_portal.views import duplicate_file_check_rename
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


class UploadTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

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
