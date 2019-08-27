from django.test import TestCase

from ..apps import S3UtilsConfig


class S3UtilsConfigTestCase(TestCase):
    def test_app_config(self):
        self.assertEqual(S3UtilsConfig.name, 's3utils')
