#
# Copyright (c) 2012-2013, Centre for Microscopy and Microanalysis
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
from unittest import skipUnless
from compare import expect
from nose.tools import ok_, eq_

import logging, base64, os, urllib2, time, urlparse
from urllib2 import HTTPError, URLError, urlopen

from tardis.tardis_portal.models import Dataset_File, Replica, Location
from tardis.tardis_portal.transfer import TransferProvider, \
    SimpleHttpTransfer, WebDAVTransfer, ScpTransfer, TransferError
from .transfer import SimpleHttpTestServer
from .transfer.generate import \
    generate_datafile, generate_dataset, generate_experiment, generate_user

logger = logging.getLogger(__name__)

def sshDir():
    return os.path.join(os.environ.get('HOME', '/'), '.ssh')

def hasDotSsh():
    return os.path.exists(sshDir())

def findKeyFile():
    if os.path.exists(os.path.join(sshDir(), 'id_dsa')):
        return os.path.join(sshDir(), 'id_dsa')
    elif os.path.exists(os.path.join(sshDir(), 'id_rsa')):
        return os.path.join(sshDir(), 'id_rsa')
    else:
        return None
    
class TransferProviderTestCase(TestCase):

    def setUp(self):
        self.user = generate_user('fred')
        Location.force_initialize()
        self.experiment = generate_experiment(users=[self.user])
        self.dataset = generate_dataset(experiments=[self.experiment])
        self.server = SimpleHttpTestServer()
        self.server.start()

    def tearDown(self):
        self.dataset.delete()
        self.experiment.delete()
        self.user.delete()
        self.server.stop()

    def testProviderInstantiation(self):
        '''
        Test that transfer_provider instantiation works
        '''

        provider = Location.get_location('test').provider
        self.assertIsInstance(provider, TransferProvider)
        self.assertIsInstance(provider, SimpleHttpTransfer)
        self.assertEqual(provider.base_url, 'http://127.0.0.1:4272/data/')
        
        provider = Location.get_location('test2').provider
        self.assertIsInstance(provider, TransferProvider)
        self.assertIsInstance(provider, WebDAVTransfer)
        self.assertFalse(401 in provider.opener.handle_error['http'])
        self.assertEqual(provider.base_url, 'http://127.0.0.1/data2/')
        
        provider = Location.get_location('test3').provider
        self.assertIsInstance(provider, TransferProvider)
        self.assertIsInstance(provider, WebDAVTransfer)
        self.assertTrue(401 in provider.opener.handle_error['http'])
        self.assertEqual(provider.base_url, 'http://127.0.0.1/data3/')

        provider = Location.get_location('scptest').provider
        self.assertIsInstance(provider, ScpTransfer)

    def testScpTransferProviderInit(self):
        with self.assertRaises(ValueError) as cm:
            ScpTransfer('xxx', 'http://localhost/', {})
        self.assertEquals(cm.exception.message, 
                          'scp: url required for transfer provider (xxx)')
        with self.assertRaises(ValueError) as cm:
            ScpTransfer('xxx', 'scp://user@localhost/', {})
        self.assertEquals(cm.exception.message, 
                          'url for transfer provider (xxx) cannot use a '
                          'username or password')
        with self.assertRaises(ValueError) as cm:
            ScpTransfer('xxx', 'scp://:passwd@localhost/', {})
        self.assertEquals(cm.exception.message, 
                          'url for transfer provider (xxx) cannot use a '
                          'username or password')

        # These won't normally be seen ...
        logger.warning('The next 3 warnings are "expected"')
        ScpTransfer('xxx', 'scp://localhost/foo?wot', {})
        ScpTransfer('xxx', 'scp://localhost/foo#frag', {})
        ScpTransfer('xxx', 'scp://localhost/foo;param', {})

    def testLocalProvider(self):
        self.do_ext_provider('sync')

    def testWebDAVProvider(self):
        self.do_ext_provider('test2')

    def testWebDAVProviderWithAuth(self):
        self.do_ext_provider('test3')

    def testSimpleHttpProvider(self):
        self.do_provider(Location.get_location('test'))

    @skipUnless(hasDotSsh() and findKeyFile(), \
                    "need user a/c with .ssh and keys")
    def testScpProvider(self):
        start_time = time.time()
        username = os.environ.get('LOGNAME', None)
        key_filename = findKeyFile()
        provider = ScpTransfer('xxx', 'scp://localhost/tmp', 
                               {'username': 'blarg',
                                'password': 'blarg', 
                                'auto_add_missing_host_key' : True})
        self.assertFalse(provider.alive())
        provider = ScpTransfer('yyy', 'scp://localhost/tmp', 
                               {'username': username,
                                'key_filename': key_filename})
        self.assertFalse(provider.alive())
        provider = ScpTransfer('yyy', 'scp://localhost/tmp', 
                               {'username': username,
                                'key_filename': key_filename, 
                                'auto_add_missing_host_key' : True})
        self.assertTrue(provider.alive())
        url = provider.put_archive('/etc/passwd', self.experiment)
        path = urlparse.urlparse(url).path
        try:
            self.assertEquals(url, 'scp://localhost/tmp/%s-archive.tar.gz' %
                              self.experiment.id)
            self.assertTrue(os.path.exists(path))
            self.assertTrue(os.path.getmtime(path) >= start_time)
            self.assertEquals(os.path.getsize(path), 
                              os.path.getsize('/etc/passwd'))
        finally:
            os.unlink(path)

    def do_ext_provider(self, loc_name):
        # This test requires an external test server configured
        # as per the 'dest_name' destination.  We skip the test is the 
        # server doesn't respond.
        loc = Location.get_location(loc_name)
        if loc.provider.alive():
            self.do_provider(loc)
        else:
            print 'SKIPPING TEST - %s server on %s is not responding\n' % \
                (loc_name, loc.url)

    def do_provider(self, loc):
        provider = loc.provider
        base_url = loc.url
        datafile, replica = generate_datafile("1/1/3", self.dataset, "Hi mum")
        self.assertEquals(replica.verify(allowEmptyChecksums=True), True)
        target_replica = Replica()
        target_replica.datafile = datafile
        target_replica.location = loc
        url = provider.generate_url(target_replica)
        self.assertEquals(url, base_url + '1/1/3')
        target_replica.url = url
        provider.put_file(replica, target_replica)

        self.assertEqual(replica.location.provider.get_file(replica).read(), 
                         "Hi mum")
        self.assertEqual(provider.get_file(target_replica).read(), "Hi mum")

        self.assertEqual(provider.get_length(target_replica), 6)

        try:
            self.maxDiff = None
            self.assertEqual(provider.get_metadata(target_replica),
                             {'sha512sum' : '2274cc8c16503e3d182ffaa835c543b' +
                              'ce278bc8fc971f3bf38b94b4d9db44cd89c8f36d4006e' +
                              '5abea29bc05f7f0ea662cb4b0e805e56bbce97f00f94e' +
                              'a6e6498', 
                              'md5sum' : '3b6b51114c3d0ad347e20b8e79765951',
                              'length' : '6'})
        except NotImplementedError:
            pass
            
        provider.remove_file(target_replica)
        with self.assertRaises(TransferError):
            provider.get_length(target_replica)

