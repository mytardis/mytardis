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
from tardis.tardis_portal.auth.localdb_auth import django_user, django_group

class UploadTestCase(TestCase):

    def setUp(self):
        from django.contrib.auth.models import User
        from os import path, mkdir
        from tempfile import mkdtemp
        from django.conf import settings
        from tardis.tardis_portal import models

        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

        self.test_dir = mkdtemp()

        self.exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                created_by=self.user,
                                )
        self.exp.save()

        self.dataset = models.Dataset(description="dataset description...",
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

        #write test file
        self.filename = "testfile.txt"

        self.f1 = open(path.join(self.test_dir, self.filename), 'w')
        self.f1.write("Test file 1")
        self.f1.close()

        self.f1_size = path.getsize(path.join(self.test_dir, self.filename))

        self.f1 = open(path.join(self.test_dir, self.filename), 'r')

    def tearDown(self):
        from shutil import rmtree

        self.f1.close()
        rmtree(self.test_dir)
        rmtree(self.dataset_path)
        rmtree(self.experiment_path)
        self.exp.delete()

    def testFileUpload(self):
        from django.http import QueryDict, HttpRequest
        from tardis.tardis_portal.views import upload
        from django.core.files import File
        from django.core.files.uploadedfile import UploadedFile
        from django.utils.datastructures import MultiValueDict
        from tardis.tardis_portal import models
        from os import path

        #create request.FILES object
        django_file = File(self.f1)
        uploaded_file = UploadedFile(file=django_file)
        uploaded_file.name = self.filename
        uploaded_file.size = self.f1_size

        post_data = [('enctype', "multipart/form-data")]
        post = QueryDict('&'.join(['%s=%s' % (k, v) for k, v in post_data]))

        files = MultiValueDict({'Filedata': [uploaded_file]})
        request = HttpRequest()
        request.FILES = files
        request.POST = post
        request.method = "POST"
        response = upload(request, self.dataset.id)
        test_files_db = models.Dataset_File.objects.filter(
            dataset__id=self.dataset.id)

        self.assertTrue(path.exists(path.join(self.dataset_path, self.filename)))
        self.assertTrue(self.dataset.id == 1)
        self.assertTrue(test_files_db[0].url == "file://1/testfile.txt")

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

class listTestCase(TestCase):

    def setUp(self):
	from django.contrib.auth.models import User, Group
        from django.test.client import Client
	from tardis.tardis_portal.models import UserProfile
        
        self.accounts = [('user1', 'pwd1'),
                         ('user2', 'pwd2'),
                         ('user3', 'pwd3')]  
        email = 'a@a.com'
        
        for uname, pwd in self.accounts:
           user = User.objects.create_user(uname, email, pwd)
           user.save()
           userProfile = UserProfile.objects.create(user=user)
           userProfile.save()

        access_uname = self.accounts[0][0]
        access_pwd = self.accounts[0][1]
        self.access_user = User.objects.get(username=access_uname)
 
        self.access_client = Client()
        login = self.access_client.login(username=access_uname, password=access_pwd)
        self.assertTrue(login)

        self.groups = ['group1',         
                  'group2',         
                  'group3',         
                  'group4']

        for groupname in self.groups:
            group = Group(name=groupname)
            group.save()

    def testGetUserList(self):
        from django.http import HttpRequest
        from tardis.tardis_portal.views import retrieve_user_list
        
        request = HttpRequest()
        request.user = self.access_user
        request.GET['authMethod'] = 'localdb'
        response = retrieve_user_list(request)

        ret_names = response.content.split(' ')
        self.assertTrue(len(ret_names) == len(self.accounts))
        print ret_names       
        for a,b in zip([u for u,p in self.accounts], ret_names):
            self.assertTrue(a == b )

    def testGetGroupList(self):

        from django.http import HttpRequest
        from tardis.tardis_portal.views import retrieve_group_list
        
        request = HttpRequest()
        request.user = self.access_user
        response = retrieve_group_list(request)

        ret_names = response.content.split(' ~ ')
        self.assertTrue(len(ret_names) == len(self.groups))

        for a,b in zip(self.groups, ret_names):
            self.assertTrue(a == b )

    def tearDown(self):
       self.access_client.logout()

class experimentAccessCase(TestCase):

    def setUp(self):
        from django.contrib.auth.models import User  
        from django.test.client import Client
        from tardis.tardis_portal.models import Experiment, ExperimentACL
 
        access_uname = 'user'
        access_pwd   = 'pwd'
        email = 'a@a.com'
  
        auth_pref = 'localdb_'

        self.access_user = User.objects.create_user(auth_pref + access_uname, email, access_pwd)

        self.access_client = Client()
        login = self.access_client.login(username=auth_pref + access_uname, password=access_pwd)
        self.assertTrue(login)

        # add an experiment which will default to being owned by the user
        # that created it         
        self.experiment = Experiment(title='title',
                         institution_name='inst_name',
                         description='description',
                         created_by=self.access_user
                               )
        self.experiment.save()
       
        acl = ExperimentACL(pluginId=django_user,
                           entityId=str(self.access_user.id),
                           experiment=self.experiment,
                           canRead=True,
                           isOwner=True,
                           aclOwnershipType=ExperimentACL.OWNER_OWNED
                           ) 
        acl.save()
        
        # Create a user which does not have ownership the experiment
        no_access_uname = 'no_access_user'
        no_access_pwd   = 'no_access_pwd'
         
        self.no_access_user = User.objects.create_user(auth_pref + no_access_uname, email, no_access_pwd)
        
        self.no_access_client = Client()
        login = self.no_access_client.login(username=auth_pref + no_access_uname, password=no_access_pwd)
        self.assertTrue(login)

        # Create the lucky individual we're going to give access to
        self.test_name = 'test_user'
        self.test_pwd  = 'pwd'
        self.test_email     = 'a@a.com'

        self.user = User.objects.create_user(auth_pref + self.test_name, self.test_email, self.test_pwd)
        self.user.save()
    
    def testAddUserAccess(self):
        from tardis.tardis_portal.views import add_experiment_access_user
        
        response = self.access_client.get('/experiment/control_panel/%i/access_list/add/user/%s?authMethod=localdb' % (self.experiment.id, self.test_name))

        # todo: how to verify correct output?
        self.assertContains(response, '<div class="access_list_user">')

    def testNoAddPermissions(self):
        from tardis.tardis_portal.views import add_experiment_access_user
        
        response = self.no_access_client.get('/experiment/control_panel/%i/access_list/add/user/%s?authMethod=localdb' % (self.experiment.id, self.test_name))

        self.assertEqual(response.status_code, 403)        

    def testAddNonExistantUser(self):
        from tardis.tardis_portal.views import add_experiment_access_user
        
        non_existant_username = 'test_boozer'
        
        response = self.access_client.get('/experiment/control_panel/%i/access_list/add/user/%s?authMethod=localdb' % (self.experiment.id, non_existant_username))
        self.assertContains(response, 'User %s does not exist' % (non_existant_username))

    def testAddToNonExistantExperiment(self):
        from tardis.tardis_portal.views import add_experiment_access_user
        from django.http import HttpRequest
        
        non_existant_id = 9999

        response = self.access_client.get('/experiment/control_panel/%i/access_list/add/user/%s?authMethod=localdb' % (non_existant_id, self.test_name))

        # Note: Ideally we'd like to check for error message, but we can't hit it with the decorator in place.
        # However, currently we check for a 403 (forbidden) error, as the 'experiment_ownership_required' decorator simply checks if 
        # the experiment_id appears in the specified user's ACL, and assumes that the absence of the experiment_id means that the 
        # experiment exists but the user doesn't have access to it. This could possibly be changed to a 404 error.  
        self.assertEqual(response.status_code, 403) 

    def testUserAlreadyHasAccess(self):
        from tardis.tardis_portal.views import add_experiment_access_user
        from django.http import HttpRequest

         # First, legitimately add the user
        response = self.access_client.get('/experiment/control_panel/%i/access_list/add/user/%s?authMethod=localdb' % (self.experiment.id, self.test_name))
        self.assertContains(response, '<div class="access_list_user">')

        # Then, try adding them again, which will generate an error message
        response = self.access_client.get('/experiment/control_panel/%i/access_list/add/user/%s?authMethod=localdb' % (self.experiment.id, self.test_name))
        #self.assertEqual(response.contents, 'User already has experiment access')

    def tearDown(self):
        pass    

class removeExperimentAccessCase(TestCase):

    def setUp(self):
        from django.contrib.auth.models import User
        from tardis.tardis_portal.models import Experiment, ExperimentACL  
        from django.test.client import Client
        
        self.auth_pref = 'localdb_'

        self.access_uname = 'user'
        access_pwd   = 'pwd'
        email = 'a@a.com' 

        self.access_user = User.objects.create_user(self.auth_pref + self.access_uname, email, access_pwd)
        self.access_client = Client()
        login = self.access_client.login(username=self.auth_pref + self.access_uname, password=access_pwd)
        self.assertTrue(login)

        self.exp_details = [{'title': 'title1', 'institution_name': 'name1', 'description': 'desc1'},
                            {'title': 'title2', 'institution_name': 'name2', 'description': 'desc2'},
                            {'title': 'title3', 'institution_name': 'name3', 'description': 'desc3'}
                           ]

        # add experiments which will default to being owned by the user
        # that created it
        for ed in self.exp_details:         
            exp = Experiment(title=ed['title'],
                                institution_name=ed['institution_name'],
                                description=ed['description'],
                                created_by=self.access_user
                                )
            exp.save()
            ed['id'] =  exp.id

            acl = ExperimentACL(pluginId=django_user,
                           entityId=str(self.access_user.id),
                           experiment=exp,
                           canRead=True,
                           isOwner=True,
                           aclOwnershipType=ExperimentACL.OWNER_OWNED
                           ) 
            acl.save()
        
        # Create a user which does not have ownership the experiment
        no_access_uname = 'no_access_user'
        no_access_pwd   = 'no_access_pwd'

        self.no_access_user = User.objects.create_user(self.auth_pref + no_access_uname, email, no_access_pwd)
        self.no_access_client = Client()
        login = self.no_access_client.login(username=self.auth_pref + no_access_uname, password=no_access_pwd)
        self.assertTrue(login)

        self.user_details = [{'name': 'user1', 'password': 'pwd1'},
                             {'name': 'user2', 'password': 'pwd2'},
                             {'name': 'user3', 'password': 'pwd3'}
                            ]
        # Create some users and give each of them access to the first experiment
        # todo make this meaningful
        for ud in self.user_details:
	    ud['user'] = User.objects.create_user(self.auth_pref + ud['name'], email, ud['password'])
            response = self.access_client.get('/experiment/control_panel/%i/access_list/add/user/%s?authMethod=localdb' % (self.exp_details[0]['id'],  ud['name']))
            self.assertContains(response, '<div class="access_list_user">')


    def testRemoveSingleUser(self):
        from tardis.tardis_portal.models import Experiment, ExperimentACL
 
        ud = self.user_details[0]
 
        response = self.access_client.get('/experiment/control_panel/%i/access_list/remove/user/%s/' % (self.exp_details[0]['id'], self.auth_pref + ud['name']))
        self.assertContains(response, 'OK')
        
        experiment = Experiment.objects.get(title=self.exp_details[0]['title'])

        acl = ExperimentACL.objects.filter(entityId=str(ud['user'].id), experiment=experiment) 
        self.assertEqual(acl.count(), 0)

          
    def testRemoveAllUsers(self):
        from tardis.tardis_portal.models import Experiment, ExperimentACL
        
        for ud in self.user_details:
            response = self.access_client.get('/experiment/control_panel/%i/access_list/remove/user/%s/' % (self.exp_details[0]['id'], self.auth_pref + ud['name']))
            self.assertContains(response, 'OK')

            experiment = Experiment.objects.get(title=self.exp_details[0]['title'])
            acl = ExperimentACL.objects.filter(entityId=str(ud['user'].id), experiment=experiment) 
            self.assertEqual(acl.count(), 0)


    def testRemoveNonExistantUser(self):
        
        non_existant_user = 'test_boozer'
 
        response = self.access_client.get('/experiment/control_panel/%i/access_list/remove/user/%s/' % (self.exp_details[0]['id'], self.auth_pref + non_existant_user))
        self.assertContains(response, "User does not exist")

    def testRemoveFromNonExistantExperiment(self):
        
        non_existant_exp = 9999
 
        response = self.access_client.get('/experiment/control_panel/%i/access_list/remove/user/%s/' % (non_existant_exp, self.auth_pref + self.user_details[0]['name']))
        # Note: The experiment ownership required decorator picks up that there is no ACL entry linking the 
        #       user and the experiment and so returns a 403 forbidden error. The check below is there 
        #       so that an assertion will fail if the decorator is ever removed and the proper functionality
        #       of the 'experiment does not exist' error needs to be confirmed 
        self.assertEqual(response.status_code, 403)
        #self.assertContains(response, "Experiment does not exist")

    def testRemoveUserWOutOwnership(self):
        from tardis.tardis_portal.models import Experiment, ExperimentACL
        
        ud = self.user_details[0]

        response = self.no_access_client.get('/experiment/control_panel/%i/access_list/remove/user/%s/' % (self.exp_details[0]['id'], self.auth_pref + self.user_details[0]['name']))
        experiment = Experiment.objects.get(title=self.exp_details[0]['title'])
        acl = ExperimentACL.objects.filter(entityId=str(ud['user'].id), experiment=experiment) 
        self.assertEqual(acl.count(), 1)

    def testRemoveOwnerPermissions(self):
        from tardis.tardis_portal.models import Experiment, ExperimentACL

        access_uname = 'user'
        access_pwd   = 'pwd'
       
        response = self.access_client.get('/experiment/control_panel/%i/access_list/remove/user/%s/' % (self.exp_details[0]['id'], self.auth_pref + self.access_uname))
        print response.content
        self.assertContains(response, 'Cannot remove your own user access')

        experiment = Experiment.objects.get(title=self.exp_details[0]['title'])

        acl = ExperimentACL.objects.filter(entityId=str(self.access_user.id), experiment=experiment) 
        self.assertEqual(acl.count(), 1)

    def tearDown(self):
        self.access_client.logout()
        self.no_access_client.logout()
