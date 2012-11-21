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

import os
from StringIO import StringIO

from django.test import TestCase
from django.test.client import Client
from django.core.management import call_command
from django.contrib.auth.models import User

from django.conf import settings
from tardis.test_settings import FILE_STORE_PATH

from tardis.apps.migration.tests import SimpleHttpTestServer
from tardis.apps.migration.tests.generate import \
    generate_datafile, generate_dataset, generate_experiment, \
    generate_user

from tardis.tardis_portal.models import Dataset

class MigrateCommandTestCase(TestCase):

    def setUp(self):
        self.dummy_dataset = Dataset()
        self.dummy_dataset.save()
        self.dummy_user = generate_user('joe')
        self.server = SimpleHttpTestServer()
        self.server.start()

    def tearDown(self):
        self.dummy_dataset.delete()
        self.dummy_user.delete()
        self.server.stop()

    def testMigrateDatafile(self):
        datafile = generate_datafile("1/2/3", self.dummy_dataset,
                                     "Hi mum", verify=False, verified=False)
        datafile2 = generate_datafile("1/2/4", self.dummy_dataset, "Hi mum")
        datafile3 = generate_datafile("1/2/5", self.dummy_dataset, "Hi mum")
        err = StringIO()
        try:
            call_command('migratefiles', 'datafile', datafile.id, stderr=err)
        except SystemExit:
            pass
        err.seek(0)
        self.assertEquals(err.read(), 
                          'Migration failed for datafile %s : ' \
                          'Only verified datafiles can be migrated ' \
                          'to this destination\n' % datafile.id)

        self.assertEquals(datafile.verify(allowEmptyChecksums=True), True)
        datafile.save()
        
        # Dry run ...
        out = StringIO()
        try:
            call_command('migratefiles', 'datafile', datafile.id, 
                         verbosity=1, stdout=out, dryRun=True)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(), 
                          'Would have migrated datafile %s\n' % datafile.id)

        # Real run, verbose
        out = StringIO()
        try:
            call_command('migratefiles', 'datafile', datafile.id, 
                         verbosity=2, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(), 
                          'Migrated datafile %s\n' % datafile.id)

        # Real run, normal
        out = StringIO()
        try:
            call_command('migratefiles', 'datafile', datafile2.id, 
                         datafile3.id, verbosity=1, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(), '') 

        # Cannot migrate a file that is not local (now)
        err = StringIO()
        try:
            call_command('migratefiles', 'datafile', datafile.id, 
                         verbosity=2, stderr=err)
        except SystemExit:
            pass
        err.seek(0)
        self.assertEquals(err.read(), 
                          'Migration failed for datafile %s : Cannot migrate '\
                              'a non-local datafile\n' % datafile.id)
                 
    def testMigrateDataset(self):
        dataset = generate_dataset()
        datafile = generate_datafile("2/2/3", dataset, "Hi mum")
        datafile2 = generate_datafile("2/2/4", dataset, "Hi mum")
        datafile3 = generate_datafile("2/2/5", dataset, "Hi mum")

        # Dry run
        out = StringIO()
        try:
            call_command('migratefiles', 'dataset', dataset.id, 
                         verbosity=2, stdout=out, dryRun=True)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(), 
                          'Would have migrated datafile %s\n'
                          'Would have migrated datafile %s\n'
                          'Would have migrated datafile %s\n' % 
                          (datafile.id, datafile2.id, datafile3.id))

        # Real run, verbose
        out = StringIO()
        try:
            call_command('migratefiles', 'dataset', dataset.id, 
                         verbosity=2, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(), 
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n' % 
                          (datafile.id, datafile2.id, datafile3.id))

    def testMigrateExperiment(self):
        dataset = generate_dataset()
        datafile = generate_datafile("3/2/3", dataset, "Hi mum")
        datafile2 = generate_datafile("3/2/4", dataset, "Hi mum")
        datafile3 = generate_datafile("3/2/5", dataset, "Hi mum")
        experiment = generate_experiment([dataset], [self.dummy_user])

        out = StringIO()
        try:
            call_command('migratefiles', 'experiment', experiment.id, 
                         verbosity=2, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(), 
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n' % 
                          (datafile.id, datafile2.id, datafile3.id))


    def testMigrateErrors(self):
        err = StringIO()
        try:
            call_command('migratefiles', 'datafile', 999, stderr=err)
        except SystemExit:
            pass
        err.seek(0)
        self.assertEquals(err.read(), 
                          'Datafile 999 does not exist\n'
                          'Error: No Datafiles selected\n')

        err = StringIO()
        try:
            call_command('migratefiles', 'datafile', 999, 
                         dest='nowhere', stderr=err)
        except SystemExit:
            pass
        err.seek(0)
        self.assertEquals(err.read(), 'Error: Destination nowhere not known\n')

    def testMigrateScore(self):
        dataset = generate_dataset()
        experiment = generate_experiment([dataset], [self.dummy_user])
        datafile = generate_datafile("3/2/3", dataset, "Hi mum")
        datafile2 = generate_datafile("3/2/4", dataset, "Hi mum")
        datafile3 = generate_datafile("3/2/5", dataset, "Hi mum")

        out = StringIO()
        try:
            call_command('migratefiles', 'score', stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'datafile %s / %s, size = 6, '
                          'score = 0.778151250384, total_size = 6\n'
                          'datafile %s / %s, size = 6, '
                          'score = 0.778151250384, total_size = 12\n'
                          'datafile %s / %s, size = 6, '
                          'score = 0.778151250384, total_size = 18\n' % 
                          (datafile.url, datafile.id, 
                           datafile2.url, datafile2.id, 
                           datafile3.url, datafile3.id))
    
    def testMigrateReclaim(self):
        dataset = generate_dataset()
        datafile = generate_datafile("3/2/3", dataset, "Hi mum")
        datafile2 = generate_datafile("3/2/4", dataset, "Hi mum")
        datafile3 = generate_datafile("3/2/5", dataset, "Hi mum")
        experiment = generate_experiment([dataset], [self.dummy_user])

        out = StringIO()
        try:
            call_command('migratefiles', 'reclaim', '11', 
                         stdout=out, verbosity=2, dryRun=True)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Would have migrated %s / %s saving 6 bytes\n'
                          'Would have migrated %s / %s saving 6 bytes\n'
                          'Would have reclaimed 12 bytes\n' %
                          (datafile.url, datafile.id, 
                           datafile2.url, datafile2.id))
        out = StringIO()
        try:
            call_command('migratefiles', 'reclaim', '11', 
                         stdout=out, verbosity=2)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Migrating %s / %s saving 6 bytes\n'
                          'Migrating %s / %s saving 6 bytes\n'
                          'Reclaimed 12 bytes\n' %
                          (datafile.url, datafile.id, 
                           datafile2.url, datafile2.id))

    def testMigrateConfig(self):
        try:
            saved = settings.DEFAULT_MIGRATION_DESTINATION
            settings.DEFAULT_MIGRATION_DESTINATION = ''
            err = StringIO()
            try:
                call_command('migratefiles', 'datafile', 999, stderr=err)
            except SystemExit:
                pass
            err.seek(0)
            self.assertEquals(err.read(), 
                              'Error: No default destination has been '
                              'configured\n')
        finally:
            settings.DEFAULT_MIGRATION_DESTINATION = saved

        try:
            saved = settings.MIGRATION_DESTINATIONS
            settings.MIGRATION_DESTINATIONS = []
            err = StringIO()
            try:
                call_command('migratefiles', 'datafile', 999, stderr=err)
            except SystemExit:
                pass
            err.seek(0)
            self.assertEquals(err.read(), 
                              'Error: Migration error: No destinations ' 
                              'have been configured\n')
        finally:
            settings.MIGRATION_DESTINATIONS = saved

