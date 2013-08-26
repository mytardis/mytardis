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

import os
from StringIO import StringIO

from django.test import TestCase
from django.test.client import Client
from django.core.management import call_command
from django.core.management.base import CommandError

from django.conf import settings
from tardis.test_settings import FILE_STORE_PATH

from tardis.tardis_portal.models import Dataset_File, Location
from tardis.tardis_portal.tests.transfer import SimpleHttpTestServer
from tardis.tardis_portal.tests.transfer.generate import \
    generate_datafile, generate_dataset, generate_experiment, \
    generate_user

from tardis.apps.migration.management.commands.migratefiles import Command


class MigrateCommandTestCase(TestCase):

    def setUp(self):
        self.dummy_user = generate_user('joe')
        self.server = SimpleHttpTestServer()
        self.server.start()
        Location.force_initialize()

    def tearDown(self):
        self.dummy_user.delete()
        self.server.stop()

    def testMirrorDatafile(self):
        dataset = generate_dataset()
        experiment = generate_experiment([dataset], [self.dummy_user])
        datafile, _ = generate_datafile(None, dataset, "Hi grandpa")

        # Dry run ...
        out = StringIO()
        try:
            call_command('migratefiles', 'mirror', 'datafile', datafile.id,
                         verbosity=1, stdout=out, dryRun=True)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Would have mirrored datafile %s\n' % datafile.id)

        # Do it
        out = StringIO()
        try:
            call_command('migratefiles', 'mirror', 'datafile', datafile.id,
                         verbosity=2, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Mirrored datafile %s\n'
                          'Transferred 1 datafiles with 0 errors\n' % datafile.id)


    def testMigrateDatafile(self):
        dataset = generate_dataset()
        experiment = generate_experiment([dataset], [self.dummy_user])
        datafile, replica = generate_datafile(None, dataset,
                                              "Hi mum", verify=False,
                                              verified=False)
        datafile2, _ = generate_datafile(None, dataset, "Hi mum")
        datafile3, _ = generate_datafile(None, dataset, "Hi mum")

        err = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'datafile',
                         datafile.id, stderr=err)
        except SystemExit:
            pass
        except CommandError as e:
            err.write(str(e))
        err.seek(0)
        self.assertEquals(err.read(),
                          'Migration failed for datafile %s : '
                          'Only verified datafiles can be migrated '
                          'to this destination\n' % datafile.id)
        self.assertEquals(replica.verify(allowEmptyChecksums=True), True)
        replica.save()

        # (Paths should all be kosher now ...)
        path = datafile.get_absolute_filepath()
        path2 = datafile2.get_absolute_filepath()
        path3 = datafile3.get_absolute_filepath()
        for p in [path, path2, path3]:
            self.assertTrue(os.path.exists(p))

        # Dry run ...
        out = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'datafile', datafile.id,
                         verbosity=1, stdout=out, dryRun=True)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Would have migrated datafile %s\n' % datafile.id)
        for p in [path, path2, path3]:
            self.assertTrue(os.path.exists(p))

        # Real run, verbose (migrates 1)
        out = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'datafile', datafile.id,
                         verbosity=3, stdout=out, stderr=StringIO())
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Migrated datafile %s\n'
                          'Transferred 1 datafiles with 0 errors\n' % datafile.id)
        for p in [path, path2, path3]:
            self.assertTrue(os.path.exists(p) == (p != path))

        # Real run, normal (migrates 2 & 3)
        out = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'datafile', datafile2.id,
                         datafile3.id, verbosity=1, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Transferred 2 datafiles with 0 errors\n')
        for p in [path, path2, path3]:
            self.assertFalse(os.path.exists(p))

        # Cannot migrate a file that is not local (now)
        err = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'datafile', datafile.id,
                         verbosity=2, stderr=err)
        except SystemExit:
            pass
        err.seek(0)
        self.assertEquals(err.read(), '') # Should "fail" silently

        # Again but with more verbosity
        err = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'datafile', datafile.id,
                         verbosity=3, stderr=err)
        except SystemExit:
            pass
        err.seek(0)
        self.assertEquals(err.read(),
                          'Source local destination test\n'
                          'No replica of %s exists at local\n' % datafile.id)

        # Real restore, verbose (restores 1, 2 & 3)
        out = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'datafile', datafile.id,
                         datafile2.id, datafile3.id, verbosity=2, stdout=out,
                         dest='local', source='test')
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Transferred 3 datafiles with 0 errors\n' %
                          (datafile.id, datafile2.id, datafile3.id))
        for p in [path, path2, path3]:
            self.assertTrue(os.path.exists(p))

        # Cannot restore files that are (now) local
        out = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'datafile', datafile.id,
                         verbosity=2, stdout=out, dest='local', source='test')
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(), # Fail quietly ... not remote
                          'Transferred 0 datafiles with 0 errors\n')

        # Now try migrating with 'no remove'
        out = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'datafile', datafile.id,
                         datafile2.id, datafile3.id, noRemove=True,
                         verbosity=2, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Transferred 3 datafiles with 0 errors\n' %
                          (datafile.id, datafile2.id, datafile3.id))
        for p in [path, path2, path3]:
            self.assertTrue(os.path.exists(p))

        # When we bring them back now, the local pathnames should change
        # because the staging code won't clobber an existing file.
        out = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'datafile', datafile.id,
                         datafile2.id, datafile3.id, verbosity=2, stdout=out,
                         dest='local', source='test')
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Transferred 3 datafiles with 0 errors\n' %
                          (datafile.id, datafile2.id, datafile3.id))
        for p, d in [(path, datafile), (path2, datafile2),
                     (path3, datafile3)]:
            dd = Dataset_File.objects.get(id=d.id)
            self.assertTrue(os.path.exists(p))
            self.assertTrue(os.path.exists(dd.get_absolute_filepath()))
            self.assertNotEqual(p, dd.get_absolute_filepath())

    def testMigrateDataset(self):
        dataset = generate_dataset()
        experiment = generate_experiment([dataset], [self.dummy_user])
        datafile, _ = generate_datafile(None, dataset, "Hi mum")
        datafile2, _ = generate_datafile(None, dataset, "Hi mum")
        datafile3, _ = generate_datafile(None, dataset, "Hi mum")

        # Dry run
        out = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'dataset', dataset.id,
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
            call_command('migratefiles', 'migrate', 'dataset', dataset.id,
                         verbosity=2, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Transferred 3 datafiles with 0 errors\n' %
                          (datafile.id, datafile2.id, datafile3.id))

        out = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'dataset', dataset.id,
                         verbosity=2, stdout=out, dest='local', source='test')
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Transferred 3 datafiles with 0 errors\n' %
                          (datafile.id, datafile2.id, datafile3.id))

    def testMigrateExperiment(self):
        dataset = generate_dataset()
        experiment = generate_experiment([dataset], [self.dummy_user])
        datafile, _ = generate_datafile(None, dataset, "Hi mum")
        datafile2, _ = generate_datafile(None, dataset, "Hi mum")
        datafile3, _ = generate_datafile(None, dataset, "Hi mum")

        out = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'experiment',
                         experiment.id,
                         verbosity=2, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Transferred 3 datafiles with 0 errors\n' %
                          (datafile.id, datafile2.id, datafile3.id))

        out = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'experiment',
                         experiment.id, dest='local', source='test',
                         verbosity=2, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Transferred 3 datafiles with 0 errors\n' %
                          (datafile.id, datafile2.id, datafile3.id))

    def testMigrateAll(self):
        dataset = generate_dataset()
        experiment = generate_experiment([dataset], [self.dummy_user])
        dataset2 = generate_dataset()
        experiment2 = generate_experiment([dataset2], [self.dummy_user])
        datafile, _ = generate_datafile(None, dataset, "Hi mum")
        datafile2, _ = generate_datafile(None, dataset, "Hi mum")
        datafile3, _ = generate_datafile(None, dataset, "Hi mum")
        datafile4, _ = generate_datafile(None, dataset2, "Hi mum")

        out = StringIO()
        try:
            call_command('migratefiles', 'migrate', all=True,
                         verbosity=2, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Transferred 4 datafiles with 0 errors\n' %
                          (datafile.id, datafile2.id, datafile3.id,
                           datafile4.id))

        out = StringIO()
        try:
            call_command('migratefiles', 'migrate', all=True,
                         verbosity=2, stdout=out, dest='local', source='test')
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Transferred 4 datafiles with 0 errors\n' %
                          (datafile.id, datafile2.id, datafile3.id,
                           datafile4.id))

    def testErrors(self):
        dataset = generate_dataset()
        generate_experiment([dataset], [self.dummy_user])
        datafile, _ = generate_datafile(None, dataset, "Hi mum")

        err = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'datafile',
                         999, stderr=err)
        except SystemExit:
            pass
        except CommandError as e:
            err.write(str(e))
        err.seek(0)
        self.assertEquals(err.read(),
                          'Datafile 999 does not exist\n'
                          'No Datafiles selected')
        err = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'datafile',
                         999, stderr=err, all=True)
        except SystemExit:
            pass
        except CommandError as e:
            err.write(str(e))
        err.seek(0)
        self.assertEquals(err.read(),
                          'No target/ids allowed with --all')

        err = StringIO()
        try:
            call_command('migratefiles', 'migrate', 'datafile', datafile.id,
                         dest='nowhere', stderr=err)
        except SystemExit:
            pass
        except CommandError as e:
            err.write(str(e))
        err.seek(0)
        self.assertEquals(err.read(), 'Destination nowhere not known')

    def testScore(self):
        dataset = generate_dataset()
        experiment = generate_experiment([dataset], [self.dummy_user])
        datafile, replica = generate_datafile(None, dataset, "Hi mum")
        datafile2, replica2 = generate_datafile(None, dataset, "Hi mum")
        datafile3, replica3 = generate_datafile(None, dataset, "Hi mum")

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
                          (replica.url, datafile.id,
                           replica2.url, datafile2.id,
                           replica3.url, datafile3.id))

    def testMigrateReclaim(self):
        dataset = generate_dataset()
        experiment = generate_experiment([dataset], [self.dummy_user])
        datafile, replica = generate_datafile(None, dataset, "Hi mum")
        datafile2, replica2 = generate_datafile(None, dataset, "Hi mum")
        datafile3, replica3 = generate_datafile(None, dataset, "Hi mum")
        url = replica.url
        url2 = replica2.url

        out = StringIO()
        try:
            call_command('migratefiles', 'reclaim', '11',
                         stdout=out, verbosity=2, dryRun=True)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Attempting to reclaim 11 bytes\n'
                          'Would have migrated %s / %s saving 6 bytes\n'
                          'Would have migrated %s / %s saving 6 bytes\n'
                          'Would have reclaimed 12 bytes\n' %
                          (url, datafile.id, url2, datafile2.id))
        out = StringIO()
        try:
            call_command('migratefiles', 'reclaim', '11',
                         stdout=out, verbosity=2)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(),
                          'Attempting to reclaim 11 bytes\n'
                          'Migrating %s / %s saving 6 bytes\n'
                          'Migrating %s / %s saving 6 bytes\n'
                          'Reclaimed 12 bytes\n'
                          'Transferred 2 datafiles with 0 errors\n' %
                          (url, datafile.id, url2, datafile2.id))

    def testMigrateEnsure(self):
        dataset = generate_dataset()
        experiment = generate_experiment([dataset], [self.dummy_user])
        datafile, _ = generate_datafile(None, dataset, "Hi mum")
        datafile2, _ = generate_datafile(None, dataset, "Hi mum")
        datafile3, _ = generate_datafile(None, dataset, "Hi mum")

        # Ensuring that there are at least zero bytes of free space
        # is a no-op ... but it tests the logic, and the method that
        # enquires how much free disc space there is.
        out = StringIO()
        try:
            call_command('migratefiles', 'ensure', '0',
                         stdout=out, verbosity=2, dryRun=True)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(), '')

    def testMigrateDestinations(self):
        # Ensuring that there are at least zero bytes of free space
        # is a no-op ... but it tests the logic, and the method that
        # enquires how much free disc space there is.
        out = StringIO()
        try:
            call_command('migratefiles', 'destinations', stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(),
            'local            : online   : local    :' +
            ' file://' + settings.FILE_STORE_PATH + '/\n' +
            'sync             : external : local    :' +
            ' file://' + settings.SYNC_TEMP_PATH + '/\n' +
            'staging          : external : local    :' +
            ' file://' + settings.STAGING_PATH + '/\n' +
            'test             : online   : http     :' +
            ' http://127.0.0.1:4272/data/\n' +
            'test2            : online   : dav      :' +
            ' http://127.0.0.1/data2/\n' +
            'test3            : online   : dav      :' +
            ' http://127.0.0.1/data3/\n')

    def testParseAmount(self):
        command = Command()
        self.assertEquals(command._parse_amount(['0']), 0)
        self.assertEquals(command._parse_amount(['1.0']), 1)
        self.assertEquals(command._parse_amount(['1.999']), 1)
        self.assertEquals(command._parse_amount(['1k']), 1024)
        self.assertEquals(command._parse_amount(['1K']), 1024)
        self.assertEquals(command._parse_amount(['1m']), 1024 * 1024)
        self.assertEquals(command._parse_amount(['1g']), 1024 * 1024 * 1024)
        self.assertEquals(command._parse_amount(['1000t']),
                          1024 * 1024 * 1024 * 1024 * 1000)
        self.assertEquals(command._parse_amount(['1.1k']), 1024 + 102)

        with self.assertRaises(CommandError) as cm:
            command._parse_amount([])
        self.assertEquals(str(cm.exception), 'missing <amount> argument')

        with self.assertRaises(CommandError) as cm:
            command._parse_amount(['1', '2'])
        self.assertEquals(str(cm.exception), 'multiple <amount> arguments')

        with self.assertRaises(CommandError) as cm:
            command._parse_amount(['abc'])
        self.assertRegexpMatches(str(cm.exception), r'.*\(abc\).*')

        with self.assertRaises(CommandError) as cm:
            command._parse_amount(['-1'])
        self.assertRegexpMatches(str(cm.exception), r'.*\(-1\).*')

        with self.assertRaises(CommandError) as cm:
            command._parse_amount(['1z'])
        self.assertRegexpMatches(str(cm.exception), r'.*\(1z\).*')

        with self.assertRaises(CommandError) as cm:
            command._parse_amount(['1.'])
        self.assertRegexpMatches(str(cm.exception), r'.*\(1\.\).*')
