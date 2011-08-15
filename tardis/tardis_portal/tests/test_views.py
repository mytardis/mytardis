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

from django.conf import settings
from django.contrib.auth import authenticate
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group

from tardis.tardis_portal.auth.localdb_auth import auth_key as localdb_auth_key
from tardis.tardis_portal.auth.localdb_auth import django_user
from tardis.tardis_portal.models import UserProfile, ExperimentACL,\
    Experiment, Dataset, Dataset_File


class UploadTestCase(TestCase):

    def setUp(self):
        from os import path, mkdir
        from tempfile import mkdtemp

        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

        self.userProfile = UserProfile(user=self.user)

        self.test_dir = mkdtemp()

        self.exp = Experiment(title='test exp1',
                institution_name='monash', created_by=self.user)
        self.exp.save()

        acl = ExperimentACL(
            pluginId=django_user,
            entityId=str(self.user.id),
            experiment=self.exp,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
            )
        acl.save()

        self.dataset = \
            Dataset(description='dataset description...',
                           experiment=self.exp)
        self.dataset.save()

        self.experiment_path = path.join(settings.FILE_STORE_PATH,
                str(self.dataset.experiment.id))

        self.dataset_path = path.join(self.experiment_path,
                                      str(self.dataset.id))

        if not path.exists(self.experiment_path):
            mkdir(self.experiment_path)
        if not path.exists(self.dataset_path):
            mkdir(self.dataset_path)

        # write test file

        self.filename = 'testfile.txt'

        self.f1 = open(path.join(self.test_dir, self.filename), 'w')
        self.f1.write('Test file 1')
        self.f1.close()

        self.f1_size = path.getsize(path.join(self.test_dir,
                                    self.filename))

        self.f1 = open(path.join(self.test_dir, self.filename), 'r')

    def tearDown(self):
        from shutil import rmtree

        self.f1.close()
        rmtree(self.test_dir)
        rmtree(self.dataset_path)
        rmtree(self.experiment_path)
        self.exp.delete()

    def testFileUpload(self):
        from os import path

        c = Client()
        c.login(username='tardis_user1', password='secret')

        response = c.post('/upload/' + str(self.dataset.id) + '/',
            {'Filedata': self.f1})

        test_files_db = \
            Dataset_File.objects.filter(dataset__id=self.dataset.id)

        self.assertTrue(path.exists(path.join(self.dataset_path,
                        self.filename)))
        self.assertTrue(self.dataset.id == 1)
        self.assertTrue(test_files_db[0].url == 'tardis://testfile.txt')

    def testUploadComplete(self):
        from django.http import QueryDict, HttpRequest
        from tardis.tardis_portal.views import upload_complete
        data = [('filesUploaded', '1'), ('speed', 'really fast!'),
                ('allBytesLoaded', '2'), ('errorCount', '0')]
        post = QueryDict('&'.join(['%s=%s' % (k, v) for (k, v) in
                         data]))
        request = HttpRequest()
        request.POST = post
        response = upload_complete(request)
        self.assertTrue('<p>Number: 1</p>' in response.content)
        self.assertTrue('<p>Errors: 0</p>' in response.content)
        self.assertTrue('<p>Bytes: 2</p>' in response.content)
        self.assertTrue('<p>Speed: really fast!</p>'
                        in response.content)


class listTestCase(TestCase):

    def setUp(self):

        self.accounts = [('user1', 'pwd1'),
                         ('user2', 'pwd2'),
                         ('user3', 'pwd3')]

        for (uname, pwd) in self.accounts:
            user = User.objects.create_user(uname, '', pwd)
            user.save()
            profile = UserProfile(user=user,
                                         isDjangoAccount=True)
            profile.save()

        self.client = Client()
        login = self.client.login(username=self.accounts[0][0],
                                  password=self.accounts[0][1])
        self.assertTrue(login)

        self.groups = ['group1', 'group2', 'group3', 'group4']
        for groupname in self.groups:
            group = Group(name=groupname)
            group.save()

    def testGetUserList(self):

        response = self.client.get('/ajax/user_list/?authMethod=%s'
                                   % localdb_auth_key)
        self.assertEqual(response.status_code, 200)
        ret_names = response.content.split(' ')
        self.assertTrue(len(ret_names) == len(self.accounts))
        for (a, b) in zip([u for (u, p) in self.accounts], ret_names):
            self.assertTrue(a == b)

    def testGetGroupList(self):

        response = self.client.get('/ajax/group_list/')
        self.assertEqual(response.status_code, 200)
        ret_names = response.content.split(' ~ ')
        self.assertTrue(len(ret_names) == len(self.groups))

        for (a, b) in zip(self.groups, ret_names):
            self.assertTrue(a == b)

    def tearDown(self):
        self.client.logout()
