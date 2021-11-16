'''
Tests for HSM app's email templates
'''
from django.contrib.auth.models import User
from django.test import TestCase

from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.datafile import DataFile
from tardis.tardis_portal.models.datafile import DataFileObject
from tardis.tardis_portal.models.storage import StorageBox

from ..email_text import email_dfo_recall_complete
from ..email_text import email_dfo_recall_failed


class HsmAppEmailTemplateTestCase(TestCase):
    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username='PUBLIC_USER_TEST')
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        self.dataset = Dataset.objects.create(description='Test')
        self.datafile = DataFile.objects.create(
            dataset=self.dataset, filename='test.txt',
            size=8, md5sum="930e419034038dfad994f0d2e602146c")
        self.storage_box = StorageBox.get_default_storage()
        self.dfo = DataFileObject.objects.create(
            datafile=self.datafile, storage_box=self.storage_box)
        self.dfo.uri = "test.txt"
        self.dfo.save()

        self.user = User.objects.create(
	    username='testuser', first_name='Test', last_name='User')

    def test_recall_complete_email(self):
        '''
        Test using the email template for a successful recall
        '''
        subject, body = email_dfo_recall_complete(self.dfo, self.user)
        self.assertEqual(subject, "[MyTardis] File recalled from archive")
        self.assertIn(
            "The following file has has been recalled from the archive",
            body)
        self.assertIn(self.datafile.filename, body)

    def test_recall_failed_email(self):
        '''
        Test using the email template for a failed recall
        '''
        subject, body = email_dfo_recall_failed(self.dfo, self.user)
        self.assertEqual(subject, "[MyTardis] File recall failed")
        self.assertIn(
            "An error occurred when attempting to recall the following file from the archive",
            body)
        self.assertIn(self.datafile.filename, body)
