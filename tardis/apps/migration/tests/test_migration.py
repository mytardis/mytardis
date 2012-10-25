from django.test import TestCase
from compare import expect
from nose.tools import ok_, eq_

import logging, base64, os, urllib2
from urllib2 import HTTPError

from tardis.tardis_portal.fetcher import get_privileged_opener
from tardis.test_settings import FILE_STORE_PATH
from tardis.apps.migration import Destination, TransferProvider, \
    SimpleHttpTransfer, MigrationError, MigrationProviderError, \
    migrate_datafile
from tardis.apps.migration.tests import SimpleHttpTestServer
from tardis.tardis_portal.models import Dataset_File, Dataset, Experiment

class MigrationTestCase(TestCase):

    def setUp(self):
        self.dummy_dataset = Dataset()
        self.dummy_dataset.save()
        self.server = SimpleHttpTestServer()
        self.server.start()

    def tearDown(self):
        self.dummy_dataset.delete()
        self.server.stop()

    def testDestination(self):
        '''
        Test that Destination instantiation works
        '''
        dest = Destination('test')
        self.assertIsInstance(dest.provider, TransferProvider)
        self.assertIsInstance(dest.provider, SimpleHttpTransfer)
        
        with self.assertRaises(ValueError):
            dest2 = Destination('unknown')

    def testProvider(self):
        provider = Destination('test').provider
        datafile = self._generate_datafile("1/2/3", "Hi mum")
        url = provider.generate_url(datafile)
        self.assertEquals(url, 'http://127.0.0.1:4272/data/1/2/3')
        provider.put_file(datafile, url)

        self.assertEqual(provider.get_file(url), "Hi mum")
        with self.assertRaises(MigrationProviderError):
            provider.get_file('https://127.0.0.1:4272/data/1/2/4')
        with self.assertRaises(HTTPError):
            provider.get_file('http://127.0.0.1:4272/data/1/2/4')

        self.assertEqual(provider.get_length(url), 6)
        with self.assertRaises(MigrationProviderError):
            provider.get_length('https://127.0.0.1:4272/data/1/2/4')
        with self.assertRaises(HTTPError):
            provider.get_length('http://127.0.0.1:4272/data/1/2/4')

        self.assertEqual(provider.get_metadata(url),
                         {'sha512sum' : '2274cc8c16503e3d182ffaa835c543bce27' +
                          '8bc8fc971f3bf38b94b4d9db44cd89c8f36d4006e5abea29b' +
                          'c05f7f0ea662cb4b0e805e56bbce97f00f94ea6e6498', 
                          'md5sum' : '3b6b51114c3d0ad347e20b8e79765951',
                          'length' : 6})
        with self.assertRaises(MigrationProviderError):
            provider.get_metadata('https://127.0.0.1:4272/data/1/2/4')
        with self.assertRaises(HTTPError):
            provider.get_metadata('http://127.0.0.1:4272/data/1/2/4')
            
        provider.remove_file(url)
        with self.assertRaises(MigrationProviderError):
            provider.get_length('https://127.0.0.1:4272/data/1/2/4')
        with self.assertRaises(HTTPError):
            provider.remove_file(url)

    def testMigration(self):
        dest = Destination('test')
        datafile = self._generate_datafile("1/2/3", "Hi mum")

        # Attempt to migrate without datafile hashes ... should
        # fail because we can't verify.
        with self.assertRaises(MigrationError):
            migrate_datafile(datafile, dest)

        # Verify sets hashes ...
        self.assertEquals(datafile.verify(allowEmptyChecksums=True), True)
        datafile.save()
        path = datafile.filename
        self.assertTrue(os.path.exists(path))

        migrate_datafile(datafile, dest)
        self.assertFalse(os.path.exists(path))

    def _generate_datafile(self, path, content):
        filepath = os.path.normpath(FILE_STORE_PATH + '/' + path)
        try:
            os.makedirs(os.path.dirname(filepath))
        except:
            pass
        file = open(filepath, 'wb+')
        file.write(content)
        file.close()
        datafile = Dataset_File()
        datafile.url = path
        datafile.mimetype = "application/unspecified"
        datafile.filename = filepath
        datafile.dataset_id = self.dummy_dataset.id
        datafile.size = str(len(content))
        datafile.save()
        return datafile

