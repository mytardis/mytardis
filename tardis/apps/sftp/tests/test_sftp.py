"""

.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""
from io import BytesIO

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import RequestFactory
from django.test import TestCase

from flexmock import flexmock
from mock import patch
from paramiko.common import AUTH_SUCCESSFUL, AUTH_FAILED
from paramiko.ssh_exception import SSHException
from paramiko.rsakey import RSAKey
from paramiko.py3compat import StringIO

from tardis.tardis_portal.download import make_mapper

from tardis.tardis_portal.models import Dataset
from tardis.tardis_portal.models import DataFile
from tardis.tardis_portal.models import DataFileObject
from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.models import ObjectACL

from tardis.apps.sftp.models import SFTPPublicKey
from tardis.apps.sftp.sftp import MyTSFTPServerInterface
from tardis.apps.sftp.sftp import MyTServerInterface
from tardis.apps.sftp.views import sftp_access
from tardis.apps.sftp.views import cybderduck_connection_window


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
            datafile_content = b"\n".join([b'some data %d' % i for i in range(1000)])
            filesize = len(datafile_content)
            datafile = DataFile(
                dataset=dataset, filename=filename, size=filesize)
            datafile.save()
            dfo = DataFileObject(
                datafile=datafile,
                storage_box=datafile.get_default_storage_box(),
                uri=url)
            dfo.file_object = BytesIO(datafile_content)
            dfo.save()
            return datafile

        saved_setting = settings.REQUIRE_DATAFILE_CHECKSUMS
        try:
            settings.REQUIRE_DATAFILE_CHECKSUMS = False
            _build(self.dataset, 'file.txt', 'path/file.txt')
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

        # should fail if user is inactive
        self.user.is_active = False
        self.user.save()

        self.assertEqual(
            server_interface.check_auth_password(self.username, self.password),
            AUTH_FAILED)

        self.user.is_active = True
        self.user.save()

    def test_sftp_key_connect(self):
        server_interface = MyTServerInterface()
        pub_key_str = (
            "AAAAB3NzaC1yc2EAAAADAQABAAAAgQCzvWE391K1pyBvePGpwDWMboSLIp"
            "5L5sMq+bXPPeJPSLOm9dnm8XexZOpeg14UpsYcmrkzVPeooaqz5PqtaHO46CdK11dS"
            "cs2a8PLnavGkJRf25/PDXxlHkiZXXbAfW+6t5aVJxSJ4Jt4FV0aDqMaaYxy4ikw6da"
            "BCkvug2OZQqQ=="
        )

        priv_key_str = """-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQCzvWE391K1pyBvePGpwDWMboSLIp5L5sMq+bXPPeJPSLOm9dnm
8XexZOpeg14UpsYcmrkzVPeooaqz5PqtaHO46CdK11dScs2a8PLnavGkJRf25/PD
XxlHkiZXXbAfW+6t5aVJxSJ4Jt4FV0aDqMaaYxy4ikw6daBCkvug2OZQqQIDAQAB
AoGASpK9XlIQD+wqafWdFpf3368O8QdI9CbnPNJkG3sKhWidmR0R7l6rEX/UOah5
hUn4km+jfWe4ZU/GGmNbmkznDdOWspDKs7eeYl7saeRzuX2CdTVvrdU7qmD5+JLk
mXlWWd6rgRIfrFYXYeDVd8p6/kPR4SJe7dTTHuEKKIt9njECQQDhMqjyoNxftpl4
+mwQu0ZDLCZ4afDCGcsf73W3oSmqLyf401vQ6KAp/PmfxqGXY0ewGMzUJn9LFOyP
WOGcDFglAkEAzFL/DI3SYmsvLMt6/vK4qwEwSiJU8byUBj3CL3eL0xjn895GXPzb
9CUMu0fz60Tn7UhbohynPLmQ2w6npbZ9NQJBAN+uujGFpl9LuFV6KCzWV4wRJoUk
dYfWpvQpnfuvkPsBq+pzxhdTeQM7y5bwbUE509MOTyXKt1WUiwQ3fKDLgiECQQCb
Z4zhSYT4ojlRQrqb6pSWS+Mkn5QoAJw9Wv+1BqHsvwa8rxSpaREKUpuqXgGhsdkM
2noHhO+V+jW4xx6vpWr5AkEAgHoSbQUR5uY8ib3N3mNowVi9NhvBN1FkwGStM9W8
QKHf8Ha+rOx3B7Dbljc+Xdpcn9VyRmDlSqzX9aCkr18mNg==
-----END RSA PRIVATE KEY-----"""
        private_key = RSAKey.from_private_key(file_obj=StringIO(priv_key_str))

        # Fail if public key not registered
        self.assertEqual(
            server_interface.check_auth_publickey(self.username, private_key),
            AUTH_FAILED
        )

        SFTPPublicKey.objects.create(
            user = self.user,
            name = "TestKey",
            key_type = "ssh-rsa",
            public_key = pub_key_str
        )

        # Succeed if public key is registered
        self.assertEqual(
            server_interface.check_auth_publickey(self.username, private_key),
            AUTH_SUCCESSFUL
        )

        # Should fail if user is inactive
        self.user.is_active = False
        self.user.save()

        self.assertEqual(
            server_interface.check_auth_publickey(self.username, private_key),
            AUTH_FAILED
        )
        self.user.is_active = True
        self.user.save()

    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_sftp_dynamic_docs_experiment(self, mock_webpack_get_bundle):
        factory = RequestFactory()
        request = factory.get(
            '/sftp_access/?object_type=experiment&object_id=%s'
            % self.exp.id)
        request.user = self.user
        response = sftp_access(request)
        path_mapper = make_mapper(settings.DEFAULT_PATH_MAPPER, rootdir=None)
        self.assertIn(
            b"sftp://tardis_user1@testserver:2200"
            b"/home/tardis_user1/experiments/%s"
            % path_mapper(self.exp).encode(),
            response.content)
        mock_webpack_get_bundle.assert_called()

    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_sftp_dynamic_docs_dataset(self, mock_webpack_get_bundle):
        factory = RequestFactory()
        request = factory.get(
            '/sftp_access/?object_type=dataset&object_id=%s'
            % self.dataset.id)
        request.user = self.user
        response = sftp_access(request)
        path_mapper = make_mapper(settings.DEFAULT_PATH_MAPPER, rootdir=None)
        self.assertIn(
            b"sftp://tardis_user1@testserver:2200"
            b"/home/tardis_user1/experiments/%s/%s"
            % (path_mapper(self.exp).encode(),
               path_mapper(self.dataset).encode()),
            response.content)
        mock_webpack_get_bundle.assert_called()

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
