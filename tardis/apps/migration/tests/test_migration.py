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

from tardis.tardis_portal.models import Dataset_File, Replica, Location
from tardis.tardis_portal.transfer import TransferError
from tardis.tardis_portal.tests.transfer import SimpleHttpTestServer
from tardis.tardis_portal.tests.transfer.generate import \
    generate_datafile, generate_dataset, generate_experiment, generate_user


from tardis.apps.migration import MigrationError, migrate_replica

class MigrationTestCase(TestCase):

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

    def testMigrateRestore(self):
        dest = Location.get_location('test')
        local = Location.get_location('local')
        datafile, replica = generate_datafile(None, self.dataset, "Hi mum",
                                              verify=False)

        # Attempt to migrate without datafile hashes ... should
        # fail because we can't verify.
        with self.assertRaises(MigrationError):
            migrate_replica(replica, dest)

        # Verify sets hashes ...
        self.assertEquals(replica.verify(allowEmptyChecksums=True), True)
        replica = Replica.objects.get(pk=replica.pk)
        path = datafile.get_absolute_filepath()
        self.assertTrue(os.path.exists(path))
        self.assertTrue(migrate_replica(replica, dest))
        self.assertFalse(os.path.exists(path))

        # Bring it back
        new_replica = datafile.get_preferred_replica()
        url = new_replica.url
        self.assertTrue(migrate_replica(new_replica, local))
        self.assertTrue(os.path.exists(path))
        # Check it was deleted remotely
        with self.assertRaises(TransferError):
            dest.provider.get_length(new_replica)

        # Refresh the datafile object because it is now stale ...
        datafile = Dataset_File.objects.get(id=datafile.id)
        replica = datafile.get_preferred_replica()

        # Repeat the process with 'noRemove'
        self.assertTrue(migrate_replica(replica, dest, noRemove=True))
        new_replica = datafile.get_preferred_replica()
        self.assertTrue(os.path.exists(path))
        self.assertEquals(dest.provider.get_length(new_replica), 6)
        migrate_replica(new_replica, local, noRemove=True)
        newpath = datafile.get_absolute_filepath()
        replica = datafile.get_preferred_replica()
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.exists(newpath))
        self.assertNotEqual(path, newpath)
        self.assertEquals(dest.provider.get_length(new_replica), 6)

    def testMirror(self):
        dest = Location.get_location('test')
        datafile, replica = generate_datafile(None, self.dataset, "Hi granny")
        path = datafile.get_absolute_filepath()
        self.assertTrue(os.path.exists(path))
        dummy_replica = Replica()
        dummy_replica.datafile = datafile
        dummy_replica.location = Location.objects.get(name='test')
        dummy_replica.url = dummy_replica.generate_default_url()

        with self.assertRaises(TransferError):
            dest.provider.get_length(dummy_replica)

        self.assertTrue(migrate_replica(replica, dest, mirror=True))
        datafile = Dataset_File.objects.get(id=datafile.id)
        self.assertTrue(datafile.is_local())
        self.assertEquals(dest.provider.get_length(dummy_replica), 9)


    def testMigrateStoreWithSpaces(self):
        dest = Location.get_location('test')
        local = Location.get_location('local')
        
        datafile, replica = generate_datafile('1/1/Hi Mum', self.dataset, 
                                              "Hi mum")
        datafile2, replica2 = generate_datafile('1/1/Hi Dad', self.dataset, 
                                                "Hi dad")

        path = datafile.get_absolute_filepath()
        self.assertTrue(os.path.exists(path))
        path2 = datafile.get_absolute_filepath()
        self.assertTrue(os.path.exists(path2))

        # Migrate them
        migrate_replica(replica, dest)
        self.assertFalse(os.path.exists(path))
        migrate_replica(replica2, dest)
        self.assertFalse(os.path.exists(path2))

        # Bring them back
        migrate_replica(datafile.get_preferred_replica(), local)
        self.assertTrue(os.path.exists(path))
        migrate_replica(datafile2.get_preferred_replica(), local)
        self.assertTrue(os.path.exists(path2))


    def testMigrationNoHashes(self):
        # Tweak the server to turn off the '?metadata' query
        self.server.server.allowQuery = False
        
        dest = Location.get_location('test')
        datafile, replica = generate_datafile("1/2/3", self.dataset, "Hi mum")
        self.assertEquals(replica.verify(allowEmptyChecksums=True), True)
        path = datafile.get_absolute_filepath()
        self.assertTrue(os.path.exists(path))
        migrate_replica(replica, dest)
        self.assertFalse(os.path.exists(path))

    def testReplicaVerify(self):
        from django.conf import settings
        saved = settings.REQUIRE_DATAFILE_CHECKSUMS
        try:
            dest = Location.get_location('test')
            datafile, replica = generate_datafile("1/2/3", self.dataset, "Hi mum")
            settings.REQUIRE_DATAFILE_CHECKSUMS = True
            self.assertTrue(replica.verify(),'Replica.verify() failed.')
            datafile.sha512sum = None
            datafile.md5sum = None
            self.assertFalse(replica.verify(), 'Replica.verify() succeeded despite no checksum (settings.REQUIRE_DATAFILE_CHECKSUMS=True).')
            self.assertFalse(replica.verify(allowEmptyChecksums=False), 'Replica.verify() succeeded despite no checksum (allowEmptyChecksums=False)')
            settings.REQUIRE_DATAFILE_CHECKSUMS = False
            datafile.sha512sum = None
            datafile.md5sum = None
            self.assertTrue(replica.verify(allowEmptyChecksums=True), 'Replica.verify() failed wrongly (allowEmptyChecksums=True)')
            datafile.sha512sum = None
            datafile.md5sum = None
            self.assertTrue(replica.verify(), 'Replica.verify() failed wrongly')
        finally:
            settings.REQUIRE_DATAFILE_CHECKSUMS = saved

