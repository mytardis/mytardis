import shutil
from os import mkdir
from os import path
from tempfile import mkdtemp
from django.test import TestCase
from django.contrib.staticfiles.management.commands import collectstatic


class CollectstaticTest(TestCase):

    def setUp(self):
        self.STATIC_ROOT = mkdtemp()
        self.NPM_ROOT_PATH = mkdtemp()
        self.cmd = collectstatic.Command()

        # Required when using django-npm's 'npm.finders.NpmFinder'
        # in settings.STATICFILES_FINDERS:
        mkdir(path.join(self.NPM_ROOT_PATH, 'node_modules'))

    def tearDown(self):
        if path.exists(self.STATIC_ROOT):
            shutil.rmtree(self.STATIC_ROOT)
        if path.exists(self.NPM_ROOT_PATH):
            shutil.rmtree(self.NPM_ROOT_PATH)

    def test_collectstatic(self):
        with self.settings(
                STATIC_ROOT=self.STATIC_ROOT,
                STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
                NPM_ROOT_PATH=self.NPM_ROOT_PATH):
            opts = {'interactive': False,
                    'verbosity': 0,
                    'link': False,
                    'clear': True,
                    'dry_run': False,
                    'ignore_patterns': [],
                    'use_default_ignore_patterns': True,
                    'post_process': True,
                    'skip_checks': True}
            self.cmd.handle(**opts)
