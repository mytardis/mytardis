"""

.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""
import os
import sys
from StringIO import StringIO
import threading

from django.conf import settings
from django.contrib.auth.models import User
from django.test.testcases import TransactionTestCase

from mock import Mock
from paramiko.common import AUTH_SUCCESSFUL

from tardis.tardis_portal.download import make_mapper

from tardis.tardis_portal.models import Dataset
from tardis.tardis_portal.models import DataFile
from tardis.tardis_portal.models import DataFileObject
from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.models import ObjectACL

from tardis.tardis_portal.sftp import MyTSFTPServerInterface
from tardis.tardis_portal.sftp import MyTServerInterface


class SFTPTest(TransactionTestCase):
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
        self.dataset.experiments = [self.exp]
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

        server = Mock(user=self.user)
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

    def tearDown(self):
        # self.server.stop()
        pass
