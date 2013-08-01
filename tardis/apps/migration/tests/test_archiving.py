#
# Copyright (c) 2013, Centre for Microscopy and Microanalysis
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

import logging, base64, os, urllib2, os.path, tarfile
from datetime import datetime
from tempfile import NamedTemporaryFile
from urllib2 import HTTPError, URLError, urlopen

from tardis.tardis_portal.models import Dataset_File, Replica, Location
from tardis.tardis_portal.transfer import TransferError
from tardis.tardis_portal.tests.transfer import SimpleHttpTestServer
from tardis.tardis_portal.tests.transfer.generate import \
    generate_datafile, generate_dataset, generate_experiment, generate_user

from tardis.apps.migration import MigrationError, last_experiment_change, \
    create_experiment_archive, save_archive_record
from tardis.apps.migration.models import Archive

class ArchivingTestCase(TestCase):

    def setUp(self):
        self.user = generate_user('fred')
        Location.force_initialize()
        self.experiment = generate_experiment(
            users=[self.user],
            title='Meanwhile, down in the archives ...',
            url='http://example.com/something')
        self.dataset = generate_dataset(experiments=[self.experiment])

    def tearDown(self):
        self.dataset.delete()
        self.experiment.delete()
        self.user.delete()

    def testCreateExperimentArchive(self):
        datafile, replica = generate_datafile(None, self.dataset, "Hi mum")
        try:
            tmp = NamedTemporaryFile(delete=False)
            archive = create_experiment_archive(self.experiment, tmp)
            self.assertTrue(os.path.exists(tmp.name))
            self.assertTrue(os.path.getsize(tmp.name) > 0)
            try:
                tf = tarfile.open(name=tmp.name, mode='r')
                members = tf.getmembers()
                self.assertEqual(len(members), 2) # manifest + one data file.
                self.assertEqual(members[0].name, 
                                 '%s/Manifest' % self.experiment.id)
                self.assertTrue(members[0].size > 0)
                self.assertEqual(members[1].name, 
                                 '%s/%s/%s' % (self.experiment.id,
                                               self.dataset.id,
                                               datafile.filename))
                self.assertEqual(members[1].size, int(datafile.size))
            finally:
                tf.close()

            self.assertEqual(archive.experiment_owner, 'fred')
            self.assertEqual(archive.nos_errors, 0)
            self.assertEqual(archive.nos_files, 1)
            self.assertEqual(archive.mimetype, 'application/x-tar')
            self.assertEqual(archive.encoding, 'x-gzip')
            self.assertEqual(archive.archive_url, None)
            self.assertEqual(archive.experiment_url, 
                             'http://example.com/something')
            self.assertEqual(archive.experiment, self.experiment)
            self.assertEqual(archive.experiment_title, 
                             'Meanwhile, down in the archives ...')

            count = Archive.objects.count()
            archive = save_archive_record(archive, 'http://example.com')
            self.assertEqual(Archive.objects.count(), count + 1)
            self.assertEqual(archive.archive_url, 
                             'http://example.com/1-1-archive.tar.gz')
            
        finally:
            os.unlink(tmp.name)

    def testLastExperimentChange(self):
        self.assertTrue(last_experiment_change(self.experiment) <
                        datetime.now())


