from django.test import TestCase

from .. import email_text


class EmailTemplates(TestCase):

    def test_pub_approved_template(self):
        subject, message = email_text.email_pub_approved(
            '_pub_title_', '_pub_url_', '_doi_', '_message_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_pub_url_' in message)
        self.assertTrue('_doi_' in message)
        self.assertTrue('_message_' in message)

        subject, message = email_text.email_pub_approved(
            '_pub_title_', '_pub_url_', None, '_message_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_pub_url_' in message)
        self.assertTrue('_doi_' not in message)
        self.assertTrue('_message_' in message)

        subject, message = email_text.email_pub_approved(
            '_pub_title_', '_pub_url_', '_doi_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_pub_url_' in message)
        self.assertTrue('_doi_' in message)
        self.assertTrue('_message_' not in message)

        subject, message = email_text.email_pub_approved(
            '_pub_title_', '_pub_url_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_pub_url_' in message)
        self.assertTrue('_doi_' not in message)
        self.assertTrue('_message_' not in message)

    def test_pub_awaiting_approval_template(self):
        subject, message = email_text.email_pub_awaiting_approval(
            '_pub_title_')
        self.assertTrue('_pub_title_' in message)

    def test_pub_rejected_template(self):
        subject, message = email_text.email_pub_rejected(
            '_pub_title_', '_message_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_message_' in message)

        subject, message = email_text.email_pub_rejected('_pub_title_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_message_' not in message)

    def test_pub_released_template(self):
        subject, message = email_text.email_pub_released(
            '_pub_title_', '_doi_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_doi_' in message)

        subject, message = email_text.email_pub_released('_pub_title_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_doi_' not in message)

    def test_pub_requires_authorisation_template(self):
        subject, message = email_text.email_pub_requires_authorisation(
            '_user_name_', '_pub_url_', '_approvals_url_')
        self.assertTrue('_user_name_' in message)
        self.assertTrue('_pub_url_' in message)
        self.assertTrue('_approvals_url_' in message)

    def test_pub_reverted_to_draft_template(self):
        subject, message = email_text.email_pub_reverted_to_draft(
            '_pub_title_', '_message_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_message_' in message)

        subject, message = email_text.email_pub_reverted_to_draft(
            '_pub_title_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_message_' not in message)
