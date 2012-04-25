from django.core import mail
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from os import path

from tardis.tardis_portal.models import Experiment
from ..models import SyncedExperiment

from .. import notify


class NotifyTestCase(TestCase):
    def setUp(self):
        self.user = User(username='user1', password='password', email='a@a.com')
        self.user.save()
        self.exp = Experiment(
                approved = True,
                title = 'title1',
                institution_name = 'institution1',
                description = 'description1',
                created_by = self.user,
                public_access = Experiment.PUBLIC_ACCESS_FULL
                )
        self.exp.save()
        self.synced_exp = SyncedExperiment(
                uid='tardis.1', experiment=self.exp, provider_url='url')
        self.synced_exp.msg = '{"message": "You broke everything!"}'
        self.synced_exp.save()

    def testGetEmailTextFail(self):
        (subject, msg) = notify._get_email_text(self.synced_exp, success=False)
        self._assertEmailContentsCorrect(subject, msg)

    def _assertEmailContentsCorrect(self, subject, msg):
        print subject
        print msg
        self.assertTrue('\n' not in subject)
        self.assertTrue('failed' in subject.lower())
        self.assertTrue('tardis.1' in msg)
        self.assertTrue('broke' in msg)

    def testEmailAdmins(self):
        mail.outbox = []
        notify.email_admins(self.synced_exp, success=False)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self._assertEmailContentsCorrect(email.subject, email.body)
        self.assertEqual(email.from_email, settings.SERVER_EMAIL)

