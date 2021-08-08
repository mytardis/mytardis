"""
test_upload_views.py

Tests for view methods relating to uploads

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
from urllib.parse import quote

from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Permission

from ...auth.localdb_auth import django_user
from ...models import ObjectACL, Experiment, Dataset, DataFile


class UploadTestCase(TestCase):

    def setUp(self):
        from os import path, mkdir
        from tempfile import mkdtemp

        user = 'tardis_user1'
        pwd = 'secret'  # nosec
        email = ''
        self.user = User.objects.create_user(user, email, pwd)
        self.user.user_permissions.add(
            Permission.objects.get(codename='change_experiment'))

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

        path_parts = [
            settings.FILE_STORE_PATH,
            "%s-%s" % (
                quote(self.dataset.description, safe='') or 'untitled',
                self.dataset.id)
            ]
        self.dataset_path = path.join(*path_parts)

        if not path.exists(self.dataset_path):
            mkdir(self.dataset_path)

        # write test file

        self.filename = 'testfile.txt'

        with open(path.join(self.test_dir, self.filename), 'w') as self.file1:
            self.file1.write('Test file 1')
            self.file1.close()

        self.file1 = open(path.join(self.test_dir, self.filename), 'r')  # pylint: disable=consider-using-with

    def tearDown(self):
        from shutil import rmtree

        self.file1.close()
        rmtree(self.test_dir)
        rmtree(self.dataset_path)
        self.exp.delete()

    def test_file_upload(self):
        from os import path

        client = Client()
        client.login(username='tardis_user1', password='secret')  # nosec
        session_id = client.session.session_key

        client.post(
            '/upload/' + str(self.dataset.id) + '/',
            {'Filedata': self.file1, 'session_id': session_id})

        test_files_db = \
            DataFile.objects.filter(dataset__id=self.dataset.id)
        self.assertTrue(
            path.exists(path.join(self.dataset_path, self.filename)))
        target_id = Dataset.objects.first().id
        self.assertEqual(self.dataset.id, target_id)
        url = test_files_db[0].file_objects.all()[0].uri
        self.assertEqual(url, path.relpath(
            '%s/testfile.txt' % self.dataset_path,
            settings.FILE_STORE_PATH))
        self.assertTrue(test_files_db[0].file_objects.all()[0].verified)

    def test_upload_complete(self):
        from django.http import QueryDict, HttpRequest
        from ...views.upload import upload_complete
        data = [('filesUploaded', '1'), ('speed', 'really fast!'),
                ('allBytesLoaded', '2'), ('errorCount', '0')]
        post = QueryDict(
            '&'.join(['%s=%s' % (k, v) for (k, v) in data]))
        request = HttpRequest()
        request.user = self.user
        request.POST = post
        response = upload_complete(request)
        self.assertTrue(b'<p>Number: 1</p>' in response.content)
        self.assertTrue(b'<p>Errors: 0</p>' in response.content)
        self.assertTrue(b'<p>Bytes: 2</p>' in response.content)
        self.assertTrue(b'<p>Speed: really fast!</p>'
                        in response.content)
