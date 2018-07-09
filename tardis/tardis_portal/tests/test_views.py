# pylint: disable=C0302
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
import json

from six.moves import urllib
from six.moves import map

from flexmock import flexmock

from django.conf import settings
from django.urls import resolve, reverse
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission

from ..staging import get_full_staging_path
from ..auth.localdb_auth import django_user
from ..models import UserAuthentication, \
    ObjectACL, Experiment, Dataset, DataFile, Schema, \
    DatafileParameterSet


class UploadTestCase(TestCase):

    def setUp(self):
        from os import path, mkdir
        from tempfile import mkdtemp

        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

        self.userProfile = self.user.userprofile

        self.test_dir = mkdtemp()

        self.exp = Experiment(title='test exp1',
                              institution_name='monash', created_by=self.user)
        self.exp.save()

        acl = ObjectACL(
            pluginId=django_user,
            entityId=str(self.user.id),
            content_object=self.exp,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED,
        )
        acl.save()

        self.dataset = \
            Dataset(description='dataset description...')
        self.dataset.save()
        self.dataset.experiments.add(self.exp)
        self.dataset.save()

        path_parts = [settings.FILE_STORE_PATH,
                      "%s-%s" % (urllib.parse.quote(self.dataset.description, safe='')
                                 or 'untitled',
                                 self.dataset.id)]
        self.dataset_path = path.join(*path_parts)

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
        self.exp.delete()

    def testFileUpload(self):
        from os import path

        c = Client()
        c.login(username='tardis_user1', password='secret')
        session_id = c.session.session_key

        c.post('/upload/' + str(self.dataset.id) + '/',
               {'Filedata': self.f1, 'session_id': session_id})

        test_files_db = \
            DataFile.objects.filter(dataset__id=self.dataset.id)
        self.assertTrue(path.exists(path.join(self.dataset_path,
                        self.filename)))
        target_id = Dataset.objects.first().id
        self.assertEqual(self.dataset.id, target_id)
        url = test_files_db[0].file_objects.all()[0].uri
        self.assertEqual(url, path.relpath(
            '%s/testfile.txt' % self.dataset_path,
            settings.FILE_STORE_PATH))
        self.assertTrue(test_files_db[0].file_objects.all()[0].verified)

    def testUploadComplete(self):
        from django.http import QueryDict, HttpRequest
        from ..views import upload_complete
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

        self.accounts = [
            ('user1', 'pwd1', 'useronefirstname', 'useronelastname'),
            ('user2', 'pwd2', 'usertwofirstname', 'usertwolastname'),
            ('user3', 'pwd3', 'userthreefirstname', 'userthreelastname')]

        for (uname, pwd, first, last) in self.accounts:
            user = User.objects.create_user(uname, '', pwd)
            user.first_name = first
            user.last_name = last
            user.save()
        self.users = User.objects.all()

        self.client = Client()
        login = self.client.login(username=self.accounts[0][0],
                                  password=self.accounts[0][1])
        self.assertTrue(login)

        self.groups = ['group1', 'group2', 'group3', 'group4']
        for groupname in self.groups:
            group = Group(name=groupname)
            group.save()

    def testGetUserList(self):

        # Match all
        response = self.client.get('/ajax/user_list/?q=')
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content)
        self.assertTrue(len(users_dict) == self.users.count())
        for user in self.users:
            user_info = [u for u in users_dict
                         if u['username'] == user.username]
            self.assertTrue(len(user_info) == 1)
            self.assertTrue(user_info[0]['first_name'] == user.first_name)
            self.assertTrue(user_info[0]['last_name'] == user.last_name)

        # Match on first name
        response = self.client.get('/ajax/user_list/?q=threefirst')
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content)

        self.assertTrue(len(users_dict) == 1)
        acct = self.users.get(username='user3')
        self.assertTrue(users_dict[0]['username'] == acct.username)
        self.assertTrue(users_dict[0]['first_name'] == acct.first_name)
        self.assertTrue(users_dict[0]['last_name'] == acct.last_name)

        # Match on last name
        response = self.client.get('/ajax/user_list/?q=twolast')
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content)

        self.assertTrue(len(users_dict) == 1)
        acct = self.users.get(username='user2')
        self.assertTrue(users_dict[0]['username'] == acct.username)
        self.assertTrue(users_dict[0]['first_name'] == acct.first_name)
        self.assertTrue(users_dict[0]['last_name'] == acct.last_name)

        # Case insensitive matching
        response = self.client.get('/ajax/user_list/?q=TWOFIRSTNAME')
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content)
        self.assertTrue(len(users_dict) == 1)
        acct = self.users.get(username='user2')
        self.assertTrue(users_dict[0]['username'] == acct.username)

        # Partial match on "first_name last_name"
        response = self.client.get(
            '/ajax/user_list/?q=onefirstname useronelast')
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content)
        self.assertTrue(len(users_dict) == 1)
        self.assertTrue(users_dict[0]['username'] == 'user1')

    def testGetGroupList(self):

        response = self.client.get('/ajax/group_list/')
        self.assertEqual(response.status_code, 200)
        ret_names = response.content.split(' ~ ')
        self.assertTrue(len(ret_names) == len(self.groups))

        for (a, b) in zip(self.groups, ret_names):
            self.assertTrue(a == b)

    def tearDown(self):
        self.client.logout()


class UserListTestCase(TestCase):
    '''
    User lists are used for autocompleting the user-to-share-with
    field when granting access to an experiment
    '''

    def setUp(self):

        self.accounts = [
            ('user1', 'pwd1', 'useronefirstname', 'useronelastname'),
            ('user2', 'pwd2', 'usertwofirstname', 'usertwolastname'),
            ('user3', 'pwd3', 'userthreefirstname', 'userthreelastname')]

        for (uname, pwd, first, last) in self.accounts:
            user = User.objects.create_user(uname, '', pwd)
            user.first_name = first
            user.last_name = last
            user.save()
        self.users = User.objects.all()

        self.client = Client()
        login = self.client.login(username=self.accounts[0][0],
                                  password=self.accounts[0][1])
        self.assertTrue(login)

    def testGetUserList(self):

        # Match all
        response = self.client.get('/ajax/user_list/?q=')
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content)
        self.assertEqual(len(self.users), len(users_dict))
        for user in self.users:
            user_info = [u for u in users_dict
                         if u['username'] == user.username]
            self.assertEqual(1, len(user_info))
            self.assertEqual(user_info[0]['first_name'], user.first_name)
            self.assertEqual(user_info[0]['last_name'], user.last_name)

        # Match on last name
        response = self.client.get('/ajax/user_list/?q=useronelastname')
        self.assertEqual(response.status_code, 200)
        users_dict = json.loads(response.content)

        self.assertEqual(len(users_dict), 1)

    def tearDown(self):
        self.client.logout()


class RightsTestCase(TestCase):

    def testRightsRequireValidOwner(self):
        # Create test owner without enough details
        username, email, password = ('testuser',
                                     'testuser@example.test',
                                     'password')
        user = User.objects.create_user(username, email, password)

        # Create test experiment and make user the owner of it
        experiment = Experiment(title='Text Experiment',
                                institution_name='Test Uni',
                                created_by=user)
        experiment.save()
        acl = ObjectACL(
            pluginId=django_user,
            entityId=str(user.id),
            content_object=experiment,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED,
        )
        acl.save()

        # Create client and login as user
        client = Client()
        login = client.login(username=username, password=password)
        self.assertTrue(login)

        # Get "Choose Rights" page, and check that we're forbidden
        rights_url = reverse('tardis.tardis_portal.views.choose_rights',
                             args=[str(experiment.id)])
        response = client.get(rights_url)
        self.assertEqual(response.status_code, 403)

        # Fill in remaining details
        user.first_name = "Voltaire"  # Mononymous persons are just fine
        user.save()

        # Get "Choose Rights" page, and check that we're now allowed access
        response = client.get(rights_url)
        self.assertEqual(response.status_code, 200)


class ManageAccountTestCase(TestCase):

    def testManageAccount(self):
        # Create test owner without enough details
        username, email, password = ('testuser',
                                     'testuser@example.test',
                                     'password')
        user = User.objects.create_user(username, email, password)
        self.assertFalse(user.userprofile.isValidPublicContact())

        manage_url = reverse('tardis.tardis_portal.views.manage_user_account')

        # Create client and go to account management URL
        client = Client()
        response = client.get(manage_url)
        # Expect redirect to login
        self.assertEqual(response.status_code, 302)

        # Login as user
        login = client.login(username=username, password=password)
        self.assertTrue(login)

        response = client.get(manage_url)
        # Expect 200 OK and a form
        self.assertEqual(response.status_code, 200)
        response.content.index('name="first_name"')
        response.content.index('name="last_name"')
        response.content.index('name="email"')
        response.content.index('value="testuser@example.test"')

        # Update account details
        response = client.post(manage_url,
                               {'first_name': 'Tommy',
                                'email': 'tommy@atkins.net'})
        # Expect 303 See Also redirect on update
        self.assertEqual(response.status_code, 303)

        user = User.objects.get(id=user.id)
        self.assertTrue(user.userprofile.isValidPublicContact())


class StageFilesTestCase(TestCase):

    def setUp(self):
        # Create test owner without enough details
        username, email, password = ('testuser',
                                     'testuser@example.test',
                                     'password')
        user = User.objects.create_user(username, email, password)
        # Need UserAuthentication
        UserAuthentication(userProfile=user.userprofile,
                           username=username,
                           authenticationMethod='localdb').save()
        # Create staging dir
        from os import path, makedirs
        staging_dir = path.join(settings.STAGING_PATH, username)
        if not path.exists(staging_dir):
            makedirs(staging_dir)
        # Ensure that staging dir is set up properly
        # assertTrue(x) checks if bool(x) is True which it is
        # when x is a non-empty string
        self.assertTrue(get_full_staging_path(username))

        # Create test experiment and make user the owner of it
        experiment = Experiment(title='Text Experiment',
                                institution_name='Test Uni',
                                created_by=user)
        experiment.save()
        acl = ObjectACL(
            pluginId=django_user,
            entityId=str(user.id),
            content_object=experiment,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED,
        )
        acl.save()

        self.dataset = \
            Dataset(description='dataset description...')
        self.dataset.save()
        self.dataset.experiments.add(experiment)
        self.dataset.save()

        self.username, self.password = (username, password)

    def _get_authenticated_client(self):
        client = Client()
        # Login as user
        login = client.login(username=self.username, password=self.password)
        self.assertTrue(login)
        # Return authenticated client
        return client

    def _get_staging_url(self):
        return reverse('tardis.tardis_portal.views.stage_files_to_dataset',
                       args=[str(self.dataset.id)])

    def testForbiddenWithoutLogin(self):
        client = Client()
        response = client.get(self._get_staging_url())
        # Expect a redirect to login
        self.assertEqual(response.status_code, 302)
        login_url = reverse('tardis.tardis_portal.views.login')
        self.assertTrue(
            login_url in response['Location'],
           "Redirect URL was not to login.")

    def testPostOnlyMethodAllowed(self):
        client = self._get_authenticated_client()

        for method in (x.lower() for x in ['GET', 'HEAD', 'PUT', 'OPTIONS']):
            response = getattr(client, method)(self._get_staging_url())
            # Expect a 405 Method Not Allowed
            self.assertEqual(response.status_code, 405)
            # Expect valid "Allow" header
            response['Allow'] = 'POST'

        response = client.post(self._get_staging_url())
        # Expect something other than a 405
        self.assertFalse(response.status_code == 405)

    def testRequiresJSON(self):
        client = Client()

        # Login as user
        login = client.login(username=self.username, password=self.password)
        self.assertTrue(login)

        response = client.post(self._get_staging_url())
        # Expect 400 Bad Request because we didn't have a payload
        self.assertEqual(response.status_code, 400)

        response = client.post(self._get_staging_url(),
                               data={'files': ['foo', 'bar']})
        # Expect 400 Bad Request because we didn't have a JSON payload
        self.assertEqual(response.status_code, 400)

        response = client.post(self._get_staging_url(),
                               data=json.dumps({'files': ['foo', 'bar']}),
                               content_type='application/octet-stream')
        # Expect 400 Bad Request because we didn't have a JSON Content-Type
        self.assertEqual(response.status_code, 400)

    def testStageFile(self):
        client = self._get_authenticated_client()

        staging_dir = get_full_staging_path(self.username)

        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile('w', dir=staging_dir) as f:
            # Write some content
            f.write('This is just some content')
            f.flush()

            data = [f.name]
            content_type = 'application/json; charset=utf-8'
            response = client.post(self._get_staging_url(),
                                   data=json.dumps(data),
                                   content_type=content_type)

            # Expect 201 Created
            self.assertEqual(response.status_code, 201)
            # Expect to get the email address of
            # staging user back
            # Can't test for async file staging
            emails = json.loads(response.content)
            self.assertEqual(len(emails), 1)


class ExperimentTestCase(TestCase):

    def setUp(self):
        # Create test owner without enough details
        username, email, password = ('testuser',
                                     'testuser@example.test',
                                     'password')
        user = User.objects.create_user(username, email, password)
        for perm in ('add_experiment', 'change_experiment'):
            user.user_permissions.add(Permission.objects.get(codename=perm))
        user.save()
        # Data used in tests
        self.user, self.username, self.password = (user, username, password)
        self.userprofile = self.user.userprofile

    def testCreateAndEdit(self):

        # Login as user
        client = Client()
        login = client.login(username=self.username, password=self.password)
        self.assertTrue(login)

        ##########
        # Create #
        ##########

        create_url = reverse('tardis.tardis_portal.views.create_experiment')

        # Check the form is accessible
        response = client.get(create_url)
        self.assertEqual(response.status_code, 200)

        # Create client and go to account management URL
        data = {'title': 'The Elements',
                'authors': 'Tom Lehrer, Arthur Sullivan',
                'institution_name': 'The University of California',
                'description':
                "There's antimony, arsenic, aluminum, selenium," +
                "And hydrogen and oxygen and nitrogen and rhenium..."
                }
        response = client.post(create_url, data=data)
        # Expect redirect to created experiment
        self.assertEqual(response.status_code, 303)
        created_url = response['Location']

        # Check that it redirects to a valid location
        response = client.get(created_url)
        self.assertEqual(response.status_code, 200)

        experiment_id = resolve(urllib.parse.urlparse(created_url).path)\
            .kwargs['experiment_id']
        experiment = Experiment.objects.get(id=experiment_id)
        for attr in ('title', 'description', 'institution_name'):
            self.assertEqual(getattr(experiment, attr), data[attr])

        # Check authors were created properly
        self.assertEqual(
            [a.author for a in experiment.experimentauthor_set.all()],
            data['authors'].split(', '))

        acl = ObjectACL.objects.get(content_type=experiment.get_ct(),
                                    object_id=experiment.id,
                                    pluginId='django_user',
                                    entityId=self.user.id)
        self.assertTrue(acl.canRead)
        self.assertTrue(acl.canWrite)
        self.assertTrue(acl.isOwner)

        ########
        # Edit #
        ########

        edit_url = reverse('tardis.tardis_portal.views.edit_experiment',
                           kwargs={'experiment_id': str(experiment_id)})

        # Check the form is accessible
        response = client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        # Create client and go to account management URL
        data = {'title': 'I Am the Very Model of a Modern Major-General',
                'authors': 'W. S. Gilbert(http://en.wikipedia.org/wiki/'
                'W._S._Gilbert), Arthur Sullivan (arthur@sullivansite.net)',
                'institution_name': 'Savoy Theatre',
                'description':
                "I am the very model of a modern Major-General," +
                "I've information vegetable, animal, and mineral,"
                }
        response = client.post(edit_url, data=data)
        # Expect redirect to created experiment
        self.assertEqual(response.status_code, 303)
        edit_url = response['Location']

        # Check that it redirects to a valid location
        response = client.get(created_url)
        self.assertEqual(response.status_code, 200)

        experiment_id = resolve(urllib.parse.urlparse(created_url).path)\
            .kwargs['experiment_id']
        experiment = Experiment.objects.get(id=experiment_id)
        for attr in ('title', 'description', 'institution_name'):
            self.assertEqual(getattr(experiment, attr), data[attr])

        # Check authors were created properly
        self.assertEqual(
            [a.author for a in experiment.experimentauthor_set.all()],
            ['W. S. Gilbert', 'Arthur Sullivan'])
        self.assertEqual(
            [a.url for a in experiment.experimentauthor_set.all()],
            ['http://en.wikipedia.org/wiki/W._S._Gilbert', None])
        self.assertEqual(
            [a.email for a in experiment.experimentauthor_set.all()],
            [None, 'arthur@sullivansite.net'])

    def testDatasetJson(self):
        user = self.user

        # Create test experiment and make user the owner of it
        def create_experiment(i):
            experiment = Experiment(title='Text Experiment #%d' % i,
                                    institution_name='Test Uni',
                                    created_by=user)
            experiment.save()
            acl = ObjectACL(
                pluginId=django_user,
                entityId=str(user.id),
                content_object=experiment,
                canRead=True,
                isOwner=True,
                aclOwnershipType=ObjectACL.OWNER_OWNED,
            )
            acl.save()
            return experiment

        experiments = list(map(create_experiment, range(1, 6)))
        experiment = experiments[0]

        # Create some datasets
        def create_dataset(i):
            ds = Dataset.objects.create(description="Dataset #%d" % i)
            ds.experiments.add(experiment)
            ds.save()
            return (ds.id, ds)
        datasets = dict(map(create_dataset, range(1, 11)))

        # Login as user
        client = Client()
        login = client.login(username=self.username, password=self.password)
        self.assertTrue(login)

        # Get JSON
        json_url = reverse(
            'tardis.tardis_portal.views.experiment_datasets_json',
            kwargs={'experiment_id': str(experiment.id)})

        # How to check items
        def check_item(item):
            self.assertIn('id', item, "Missing dataset ID")
            dataset = datasets[item['id']]
            # Check attributes
            self.assertEqual(item['description'], dataset.description)
            self.assertEqual(item['immutable'], dataset.immutable)
            # todo - put ye test back
            # Check experiment list is the same
            self.assertEqual(
                frozenset(item['experiments']),
                frozenset(dataset.experiments .values_list('id', flat=True)))

        # Check the JSON
        response = client.get(json_url)
        self.assertEqual(response.status_code, 200)
        items = json.loads(response.content)
        for item in items:
            check_item(item)
            # Check there's an individual resource
            response = client.get(json_url+str(item['id']))
            self.assertEqual(response.status_code, 200)
            item = json.loads(response.content)
            check_item(item)
            # Attempt to remove the dataset from the original experiment
            # Should fail because it would leave the dataset orphaned
            response = client.delete(json_url+str(item['id']),
                                     content_type='application/json')
            self.assertEqual(response.status_code, 403)
            # Add the dataset to another experiment with PUT
            new_url = reverse('tardis.tardis_portal.views.dataset_json',
                              kwargs={'experiment_id': str(experiments[1].id),
                                      'dataset_id': item['id']})
            response = client.put(new_url,
                                  data=json.dumps(item),
                                  content_type='application/json')
            item = json.loads(response.content)
            check_item(item)
            # This dataset should now have two experiments
            self.assertEqual(
                sorted(item['experiments']),
                sorted([e.id for e in experiments[:2]]))
            # Add the rest of the experiments to the dataset
            item['experiments'] = [e.id for e in experiments]
            # Send the revised dataset back to be altered with PUT
            response = client.put(json_url+str(item['id']),
                                  data=json.dumps(item),
                                  content_type='application/json')
            self.assertEqual(response.status_code, 200)
            item = json.loads(response.content)
            check_item(item)
            self.assertEqual(
                sorted(item['experiments']),
                sorted([e.id for e in experiments]))
            # Remove the dataset from the original experiment
            # Should succeed because there are now many more experiments
            response = client.delete(json_url+str(item['id']),
                                     content_type='application/json')
            self.assertEqual(response.status_code, 200)
            item = json.loads(response.content)
            check_item(item)
            # Expect the item is now in all but the first experiment
            self.assertEqual(
                sorted(item['experiments']),
                sorted([e.id for e in experiments][1:]))
            # Check it no longer exists
            response = client.get(json_url+str(item['id']))
            self.assertEqual(response.status_code, 404)


class ContextualViewTest(TestCase):

    def setUp(self):
        """
        setting up essential objects, copied from tests above
        """
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)
        self.userProfile = self.user.userprofile
        self.exp = Experiment(title='test exp1',
                              institution_name='monash', created_by=self.user)
        self.exp.save()
        self.acl = ObjectACL(
            pluginId=django_user,
            entityId=str(self.user.id),
            content_object=self.exp,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED,
        )
        self.acl.save()
        self.dataset = Dataset(description='dataset description...')
        self.dataset.save()
        self.dataset.experiments.add(self.exp)
        self.dataset.save()

        self.datafile = DataFile(dataset=self.dataset,
                                 size=42, filename="foo",
                                 md5sum="junk")
        self.datafile.save()

        self.testschema = Schema(namespace="http://test.com/test/schema",
                                 name="Test View",
                                 type=Schema.DATAFILE,
                                 hidden=True)
        self.testschema.save()
        self.dfps = DatafileParameterSet(datafile=self.datafile,
                                         schema=self.testschema)
        self.dfps.save()

    def tearDown(self):
        self.user.delete()
        self.exp.delete()
        self.dataset.delete()
        self.datafile.delete()
        self.testschema.delete()
        self.dfps.delete()
        self.acl.delete()

    def testDetailsDisplay(self):
        """
        test display of view for an existing schema and no display for an
        undefined one.
        """
        from ..views import display_datafile_details
        request = flexmock(user=self.user, groups=[("testgroup", flexmock())])
        with self.settings(DATAFILE_VIEWS=[
                ("http://test.com/test/schema", "/test/url"),
                ("http://does.not.exist", "/false/url")]):
            response = display_datafile_details(
                request, datafile_id=self.datafile.id)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("/ajax/parameters/" in response.content)
            self.assertTrue("/test/url" in response.content)
            self.assertFalse("/false/url" in response.content)


class ViewTemplateContextsTest(TestCase):

    def setUp(self):
        """
        setting up essential objects, copied from tests above
        """

        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)
        self.userProfile = self.user.userprofile
        self.exp = Experiment(title='test exp1',
                              institution_name='monash', created_by=self.user)
        self.exp.save()
        self.acl = ObjectACL(
            pluginId=django_user,
            entityId=str(self.user.id),
            content_object=self.exp,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED,
        )
        self.acl.save()
        self.dataset = Dataset(description='dataset description...')
        self.dataset.save()
        self.dataset.experiments.add(self.exp)
        self.dataset.save()

        self.datafile = DataFile(dataset=self.dataset,
                                 size=42, filename="foo",
                                 md5sum="junk")
        self.datafile.save()

    def tearDown(self):
        self.user.delete()
        self.exp.delete()
        self.dataset.delete()
        self.datafile.delete()
        self.acl.delete()

    def testExperimentView(self):
        """
        test some template context parameters for an experiment view
        """
        from ..views import ExperimentView
        from django.http import HttpRequest
        import sys

        # Default behavior
        views_module = flexmock(sys.modules['tardis.tardis_portal.views'])
        request = HttpRequest()
        request.method = 'GET'
        request.user = self.user
        request.groups = []
        context = {'organization': ['test', 'test2'],
                   'default_organization': 'test',
                   'default_format': 'tar',
                   'protocol': [['tgz', '/download/experiment/1/tgz/'],
                                ['tar', '/download/experiment/1/tar/']]}
        views_module.should_call('render_response_index'). \
            with_args(_AnyMatcher(), "tardis_portal/view_experiment.html",
                      _ContextMatcher(context))
        view_fn = ExperimentView.as_view()
        response = view_fn(request, experiment_id=self.exp.id)
        self.assertEqual(response.status_code, 200)

        # Behavior with USER_AGENT_SENSING enabled and a request.user_agent
        saved_setting = getattr(settings, "USER_AGENT_SENSING", None)
        try:
            setattr(settings, "USER_AGENT_SENSING", True)
            request = HttpRequest()
            request.method = 'GET'
            request.user = self.user
            request.groups = []
            mock_agent = _MiniMock(os=_MiniMock(family="Macintosh"))
            setattr(request, 'user_agent', mock_agent)
            context = {'organization': ['classic', 'test', 'test2'],
                       'default_organization': 'classic',
                       'default_format': 'tar',
                       'protocol': [['tar', '/download/experiment/1/tar/']]}
            views_module.should_call('render_response_index'). \
                with_args(_AnyMatcher(), "tardis_portal/view_experiment.html",
                          _ContextMatcher(context))
            view_fn = ExperimentView.as_view()
            response = view_fn(request, experiment_id=self.exp.id)
            self.assertEqual(response.status_code, 200)
        finally:
            if saved_setting is not None:
                setattr(settings, "USER_AGENT_SENSING", saved_setting)
            else:
                delattr(settings, "USER_AGENT_SENSING")

    def testDatasetView(self):
        """
        test some context parameters for a dataset view
        """
        from ..views import DatasetView
        from django.http import HttpRequest
        import sys

        views_module = flexmock(sys.modules['tardis.tardis_portal.views'])
        request = HttpRequest()
        request.method = 'GET'
        request.user = self.user
        request.groups = []
        context = {'default_organization': 'test',
                   'default_format': 'tar'}
        views_module.should_call('render_response_index'). \
            with_args(_AnyMatcher(), "tardis_portal/view_dataset.html",
                      _ContextMatcher(context))
        view_fn = DatasetView.as_view()
        response = view_fn(request, dataset_id=self.dataset.id)
        self.assertEqual(response.status_code, 200)

        # Behavior with USER_AGENT_SENSING enabled and a request.user_agent
        saved_setting = getattr(settings, "USER_AGENT_SENSING", None)
        try:
            setattr(settings, "USER_AGENT_SENSING", True)
            request = HttpRequest()
            request.method = 'GET'
            request.user = self.user
            request.groups = []
            mock_agent = _MiniMock(os=_MiniMock(family="Macintosh"))
            setattr(request, 'user_agent', mock_agent)
            context = {'default_organization': 'classic',
                       'default_format': 'tar'}
            views_module.should_call('render_response_index'). \
                with_args(_AnyMatcher(), "tardis_portal/view_dataset.html",
                          _ContextMatcher(context))
            view_fn = DatasetView.as_view()
            response = view_fn(request, dataset_id=self.dataset.id)
            self.assertEqual(response.status_code, 200)
        finally:
            if saved_setting is not None:
                setattr(settings, "USER_AGENT_SENSING", saved_setting)
            else:
                delattr(settings, "USER_AGENT_SENSING")


class ExperimentListsTest(TestCase):

    def setUp(self):
        """
        setting up essential objects, copied from tests above
        """

        self.username = 'tardis_user1'
        self.password = 'secret'
        email = ''
        self.user = User.objects.create_user(self.username, email, self.password)
        self.exps = []
        self.acls = []
        for exp_num in range(1, 301):
            exp = Experiment.objects.create(title="Experiment %s" % exp_num,
                                            created_by=self.user)
            self.exps.append(exp)
            isOwner = exp_num <= 100
            acl = ObjectACL.objects.create(
                pluginId=django_user,
                entityId=str(self.user.id),
                content_object=exp,
                canRead=True,
                isOwner=isOwner,
                aclOwnershipType=ObjectACL.OWNER_OWNED)
            self.acls.append(acl)

    def tearDown(self):
        self.user.delete()
        for exp in self.exps:
            exp.delete()
        for acl in self.acls:
            acl.delete()

    def testMyDataView(self):
        """
        Test My Data view
        """
        from django.http import QueryDict, HttpRequest
        from ..views import my_data
        from ..views import retrieve_owned_exps_list
        from ..views import retrieve_shared_exps_list

        request = HttpRequest()
        request.method = 'GET'
        request.user = self.user
        response = my_data(request)
        self.assertEqual(response.status_code, 200)
        # jQuery hasn't populated the divs yet:
        self.assertIn('<div id="myowned" class="mydata accordion"></div>',
                      response.content)
        self.assertIn('<div id="myshared" class="mydata accordion"></div>',
                      response.content)

        # Owned experiments:
        self.assertEqual(settings.OWNED_EXPS_PER_PAGE, 20)
        self.assertEqual(len([acl for acl in self.acls if acl.isOwner]),
                         100)
        request.GET = QueryDict('')
        response = retrieve_owned_exps_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('<div class="pagination">', response.content)
        self.assertIn('Page 1 of 5', response.content)

        # Test page number greater than num_pages,
        # should just give the last page (5).
        request.GET = QueryDict('page=6')
        response = retrieve_owned_exps_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('<div class="pagination">', response.content)
        self.assertIn('Page 5 of 5', response.content)

        # Now let's reduce the number of owned experiments from
        # 100 to 10, so pagination isn't needed:
        deleted_count = 0
        for acl in list(self.acls):
            exp = Experiment.objects.get(id=acl.object_id)
            if acl.isOwner and deleted_count < 90:
                self.exps.remove(exp)
                self.acls.remove(acl)
                exp.delete()
                acl.delete()
                deleted_count += 1
        request.GET = QueryDict('')
        response = retrieve_owned_exps_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('<div class="pagination">', response.content)

        # Shared experiments:
        self.assertEqual(settings.SHARED_EXPS_PER_PAGE, 20)
        self.assertEqual(len([acl for acl in self.acls if not acl.isOwner]),
                         200)
        request.GET = QueryDict('')
        response = retrieve_shared_exps_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('<div class="pagination">', response.content)
        self.assertIn('Page 1 of 10', response.content)

        # Test page number greater than num_pages,
        # should just give the last page (10).
        request.GET = QueryDict('page=12')
        response = retrieve_shared_exps_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('<div class="pagination">', response.content)
        self.assertIn('Page 10 of 10', response.content)

        # Now let's reduce the number of shared experiments from
        # 200 to 10, so pagination isn't needed:
        deleted_count = 0
        for acl in list(self.acls):
            exp = Experiment.objects.get(id=acl.object_id)
            if not acl.isOwner and deleted_count < 190:
                self.exps.remove(exp)
                self.acls.remove(acl)
                exp.delete()
                acl.delete()
                deleted_count += 1
        request.GET = QueryDict('')
        response = retrieve_shared_exps_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('<div class="pagination">', response.content)


class _ContextMatcher(object):
    def __init__(self, template):
        self.template = template

    def __eq__(self, other):
        for (key, value) in self.template.items():
            if key not in other or other[key] != value:
                return False
        return True


class _AnyMatcher(object):
    def __eq__(self, other):
        return True


class _MiniMock(object):
    def __new__(cls, **attrs):
        result = object.__new__(cls)
        result.__dict__ = attrs
        return result
