#
# Copyright (c) 2012, Centre for Microscopy and Microanalysis
#   (University of Queensland, Australia)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the  University of Queensland nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
#

from django.test import TestCase
from compare import expect
from nose.tools import ok_, eq_

import logging, base64, os, urllib2
from urllib2 import HTTPError, URLError, urlopen

from tardis.tardis_portal.fetcher import get_privileged_opener
from tardis.test_settings import FILE_STORE_PATH
from tardis.apps.migration import Destination, TransferProvider, \
    SimpleHttpTransfer, WebDAVTransfer, MigrationError, \
    MigrationProviderError, migrate_datafile, restore_datafile
from tardis.apps.migration.tests import SimpleHttpTestServer
from tardis.apps.migration.tests.generate import \
    generate_datafile, generate_dataset, generate_experiment, generate_user
from tardis.tardis_portal.models import Dataset_File, Dataset, Experiment

class MigrationTestCase(TestCase):

    def setUp(self):
        self.user = generate_user('fred')
        self.experiment = generate_experiment(users=[self.user])
        self.dataset = generate_dataset(experiments=[self.experiment])
        self.server = SimpleHttpTestServer()
        self.server.start()

    def tearDown(self):
        self.dataset.delete()
        self.experiment.delete()
        self.user.delete()
        self.server.stop()

    def testDestination(self):
        '''
        Test that Destination instantiation works
        '''
        dest = Destination.get_destination('test')
        self.assertIsInstance(dest.provider, TransferProvider)
        self.assertIsInstance(dest.provider, SimpleHttpTransfer)
        
        dest = Destination.get_destination('test2')
        self.assertIsInstance(dest.provider, TransferProvider)
        self.assertIsInstance(dest.provider, WebDAVTransfer)
        
        dest = Destination.get_destination('test3')
        self.assertIsInstance(dest.provider, TransferProvider)
        self.assertIsInstance(dest.provider, WebDAVTransfer)
        
        dest2 = Destination.get_destination('test3')
        self.assertEqual(dest, dest2)

        with self.assertRaises(ValueError):
            dest2 = Destination.get_destination('unknown')

    def testWebDAVProvider(self):
        self.do_ext_provider('test2')

    def testWebDAVProviderWithAuth(self):
        self.do_ext_provider('test3')

    def testSimpleHttpProvider(self):
        self.do_provider(Destination.get_destination('test'))

    def do_ext_provider(self, dest_name):
        # This test requires an external test server configured
        # as per the 'dest_name' destination.  We skip the test is the 
        # server doesn't respond.
        try:
            dest = Destination.get_destination(dest_name)
            dest.opener.open(dest.base_url)
        except URLError:
            print 'SKIPPING TEST - %s server on %s not responding\n' % \
                (dest_name, dest.base_url)
            return
        self.do_provider(dest)

    def do_provider(self, dest):
        provider = dest.provider
        base_url = dest.base_url
        datafile = generate_datafile("1/2/3", self.dataset, "Hi mum")
        self.assertEquals(datafile.verify(allowEmptyChecksums=True), True)
        url = provider.generate_url(datafile)
        self.assertEquals(url, base_url + '1/2/3')
        provider.put_file(datafile, url)

        self.assertEqual(provider.get_file(url), "Hi mum")
        with self.assertRaises(MigrationProviderError):
            provider.get_file('http://foo/data/1/2/4')
        with self.assertRaises(HTTPError):
            provider.get_file(base_url + '1/2/4')

        self.assertEqual(provider.get_length(url), 6)
        with self.assertRaises(MigrationProviderError):
            provider.get_length('http://foo/data/1/2/4')
        with self.assertRaises(HTTPError):
            provider.get_length(base_url + '1/2/4')

        try:
            self.assertEqual(provider.get_metadata(url),
                             {'sha512sum' : '2274cc8c16503e3d182ffaa835c543b' +
                              'ce278bc8fc971f3bf38b94b4d9db44cd89c8f36d4006e' +
                              '5abea29bc05f7f0ea662cb4b0e805e56bbce97f00f94e' +
                              'a6e6498', 
                              'md5sum' : '3b6b51114c3d0ad347e20b8e79765951',
                              'length' : 6})
            with self.assertRaises(MigrationProviderError):
                provider.get_metadata('http:/foo/data/1/2/4')
                with self.assertRaises(HTTPError):
                    provider.get_metadata(base_url + '1/2/4')
        except NotImplementedError:
            pass
            
        provider.remove_file(url)
        with self.assertRaises(MigrationProviderError):
            provider.get_length('http://foo/data/1/2/4')
        with self.assertRaises(HTTPError):
            provider.remove_file(url)

    def testMigration(self):
        dest = Destination.get_destination('test')
        
        datafile = generate_datafile(None, self.dataset, "Hi mum",
                                     verify=False)

        # Attempt to migrate without datafile hashes ... should
        # fail because we can't verify.
        with self.assertRaises(MigrationError):
            migrate_datafile(datafile, dest)

        # Verify sets hashes ...
        self.assertEquals(datafile.verify(allowEmptyChecksums=True), True)
        datafile.save()
        path = datafile.get_absolute_filepath()
        self.assertTrue(os.path.exists(path))
        migrate_datafile(datafile, dest)
        self.assertFalse(os.path.exists(path))

        # Bring it back
        restore_datafile(datafile)
        self.assertTrue(os.path.exists(path))

    def testMigrationNoHashes(self):
        # Tweak the server to turn off the '?metadata' query
        self.server.server.allowQuery = False
        
        dest = Destination.get_destination('test')
        datafile = generate_datafile("1/2/3", self.dataset, "Hi mum")
        self.assertEquals(datafile.verify(allowEmptyChecksums=True), True)
        datafile.save()
        path = datafile.get_absolute_filepath()
        self.assertTrue(os.path.exists(path))
        migrate_datafile(datafile, dest)
        self.assertFalse(os.path.exists(path))


