import shutil
from os import makedirs, path
from django.test import TestCase
from django.conf import settings
from django.core import management


class CollectstaticTest(TestCase):

    def setUp(self):
        if not path.exists(settings.STATIC_ROOT):
            makedirs(settings.STATIC_ROOT)

    def tearDown(self):
        if path.exists(settings.STATIC_ROOT):
            shutil.rmtree(settings.STATIC_ROOT)

    def test_collectstatic(self):
        management.call_command(
            'collectstatic',
            '--clear',
            '--settings',
            'tardis.test_settings',
            '-v',
            '0',
            interactive=False)
