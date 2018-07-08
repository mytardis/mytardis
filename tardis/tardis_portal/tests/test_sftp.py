"""

.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""
from StringIO import StringIO

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import RequestFactory
from django.test import TestCase

from flexmock import flexmock
from paramiko.common import AUTH_SUCCESSFUL
from paramiko.ssh_exception import SSHException

from ..download import make_mapper

from ..models import Dataset
from ..models import DataFile
from ..models import DataFileObject
from ..models import Experiment
from ..models import ObjectACL

from ..sftp import MyTSFTPServerInterface
from ..sftp import MyTServerInterface

from ..views.pages import sftp_access
from ..views.images import cybderduck_connection_window


class SFTPTest(TestCase):
    def setUp(self):
        self.hostname = '127.0.0.1'
        self.username = 'tardis_user1'
        self.password = 'secret'
        email = ''
        self.user = User.objects.create_user(
            self.username, email, self.password)
        self.exp = Experiment(
            title='test exp1', institution_name='monash', created_by=self.user)
        self.exp.save()

        self.acl = ObjectACL(
            content_object=self.exp,
            pluginId='django_user',
            entityId=str(self.user.id),
            isOwner=True,
            canRead=True,
            canWrite=True,
            canDelete=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED)
        self.acl.save()

        self.dataset = Dataset(description='test dataset1')
        self.dataset.save()
        self.dataset.experiments.set([self.exp])
        self.dataset.save()

        def _build(dataset, filename, url):
            datafile_content = "\n".join(['some data %d' % i
                                          for i in range(1000)])
            filesize = len(datafile_content)
            datafile = DataFile(
                dataset=dataset, filename=filename, size=filesize)
            datafile.save()
            dfo = DataFileObject(
                datafile=datafile,
                storage_box=datafile.get_default_storage_box(),
                uri=url)
            dfo.file_object = StringIO(datafile_content)
            dfo.save()
            return datafile

        saved_setting = settings.REQUIRE_DATAFILE_CHECKSUMS
        try:
            settings.REQUIRE_DATAFILE_CHECKSUMS = False
            df_file = _build(self.dataset, 'file.txt', 'path/file.txt')
        finally:
            settings.REQUIRE_DATAFILE_CHECKSUMS = saved_setting

    def test_sftp(self):
        path_mapper = make_mapper(settings.DEFAULT_PATH_MAPPER, rootdir=None)

        server = flexmock(user=self.user)
        sftp_interface = MyTSFTPServerInterface(server=server)
        sftp_interface.session_started()

        exp_sftp_folders = sftp_interface.list_folder(
            '/home/%s/experiments/' % self.username)
        exp_sftp_folder_names = sorted(
            [sftp_folder.filename for sftp_folder in exp_sftp_folders])
        exp_folder_names = sorted(
                [path_mapper(exp) for exp in Experiment.safe.all(self.user)])
        self.assertEqual(exp_sftp_folder_names, exp_folder_names)

        ds_sftp_folders = sftp_interface.list_folder(
            '/home/%s/experiments/%s/'
            % (self.username, path_mapper(self.exp)))
        ds_sftp_folder_names = sorted(
            [sftp_folder.filename for sftp_folder in ds_sftp_folders])
        self.assertEqual(
            ds_sftp_folder_names,
            ['00_all_files', path_mapper(self.dataset)])

        sftp_files = sftp_interface.list_folder(
            '/home/%s/experiments/%s/%s/'
            % (self.username, path_mapper(self.exp),
               path_mapper(self.dataset)))
        sftp_filenames = sorted(
            [sftp_file.filename for sftp_file in sftp_files])
        self.assertEqual(sftp_filenames, ['file.txt'])

        server_interface = MyTServerInterface()
        self.assertEqual(
            server_interface.check_auth_password(self.username, self.password),
            AUTH_SUCCESSFUL)

    def test_sftp_dynamic_docs_experiment(self):
        factory = RequestFactory()
        request = factory.get(
            '/sftp_access/?object_type=experiment&object_id=%s'
            % self.exp.id)
        request.user = self.user
        response = sftp_access(request)
        path_mapper = make_mapper(settings.DEFAULT_PATH_MAPPER, rootdir=None)
        self.assertIn(
            "sftp://tardis_user1@testserver:2200"
            "/home/tardis_user1/experiments/%s"
            % path_mapper(self.exp),
            response.content)

    def test_sftp_dynamic_docs_dataset(self):
        factory = RequestFactory()
        request = factory.get(
            '/sftp_access/?object_type=dataset&object_id=%s'
            % self.dataset.id)
        request.user = self.user
        response = sftp_access(request)
        path_mapper = make_mapper(settings.DEFAULT_PATH_MAPPER, rootdir=None)
        self.assertIn(
            "sftp://tardis_user1@testserver:2200"
            "/home/tardis_user1/experiments/%s/%s"
            % (path_mapper(self.exp), path_mapper(self.dataset)),
            response.content)

    def test_cybderduck_connection_window(self):
        factory = RequestFactory()
        request = factory.get('/sftp_access/cyberduck/connection.png')
        request.user = self.user
        response = cybderduck_connection_window(request)
        self.assertEqual(response.status_code, 200)


class SFTPDManagementTestCase(TestCase):

    def testSFTPDWithoutHostKey(self):
        '''
        Attempting to start the SFTPD service without a host key
        should raise an SSHException
        '''
        saved_setting = settings.SFTP_HOST_KEY
        settings.SFTP_HOST_KEY = ''
        with self.assertRaises(SSHException):
            call_command('sftpd')
        settings.SFTP_HOST_KEY = saved_setting
