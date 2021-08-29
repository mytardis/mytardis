from django.test import TestCase

from .. import email_text


class EmailTemplates(TestCase):

    def test_pub_rejected_template(self):
        _subject, message = email_text.email_pub_rejected(
            '_pub_title_', '_message_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_message_' in message)

        _subject, message = email_text.email_pub_rejected('_pub_title_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_message_' not in message)

    def test_pub_released_template(self):
        _subject, message = email_text.email_pub_released(
            '_pub_title_', '_doi_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_doi_' in message)

        _subject, message = email_text.email_pub_released('_pub_title_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_doi_' not in message)

    def test_pub_reverted_to_draft_template(self):
        _subject, message = email_text.email_pub_reverted_to_draft(
            '_pub_title_', '_message_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_message_' in message)

        _subject, message = email_text.email_pub_reverted_to_draft(
            '_pub_title_')
        self.assertTrue('_pub_title_' in message)
        self.assertTrue('_message_' not in message)
