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

import os, datetime
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

from tardis.apps.migration.models import Archive
from tardis.apps.migration.management.commands.archive import Command


class ArchiveCommandTestCase(TestCase):

    def setUp(self):
        self.dummy_user = generate_user('joe')
        self.server = SimpleHttpTestServer()
        self.server.start()
        Location.force_initialize()

    def tearDown(self):
        self.dummy_user.delete()
        self.server.stop()

    def testArchiveExperiment(self):
        now = datetime.datetime.now()
        dataset = generate_dataset()
        experiment = generate_experiment([dataset], [self.dummy_user])
        datafile, _ = generate_datafile(None, dataset, "Hi grandpa")
        datafile2, _ = generate_datafile(None, dataset, "Hi grandma", time=now)
        archtest = Location.get_location('archtest')

        # Dry run ...
        out = StringIO()
        try:
            call_command('archive', experiment.id, 
                         verbosity=1, stdout=out, dryRun=True)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(), 
                          'Would have archived experiment %s\n' % experiment.id)

        # Dry run ... all
        out = StringIO()
        try:
            call_command('archive', all=True,
                         verbosity=1, stdout=out, dryRun=True)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(out.read(), 
                          'Would have archived experiment %s\n' % experiment.id)

        # Do one ... to file
        out = StringIO()
        try:
            call_command('archive', experiment.id, directory='/tmp',
                         verbosity=1, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(), 
            'Archived experiment %s to /tmp/%s-archive.tar.gz\n' \
            'Archived 1 experiments with 0 errors\n' % \
                (experiment.id, experiment.id))

        # Do one ... to archtest
        out = StringIO()
        try:
            call_command('archive', experiment.id, location='archtest',
                         verbosity=1, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(), 
            'Archived experiment %s to %s%s-1-archive.tar.gz\n' \
                'Archived 1 experiments with 0 errors\n' % \
                (experiment.id, archtest.provider.base_url, 
                 experiment.id))
        
        # Repeat to archtest ... incremental (no change)
        out = StringIO()
        try:
            call_command('archive', experiment.id, location='archtest',
                         incremental=True, verbosity=1, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(), 
            'Archived 0 experiments with 0 errors\n')

        # Repeat to archtest ... incremental (changed)
        datafile2 = Dataset_File.objects.get(id=datafile2.id)
        datafile2.modification_time = now + datetime.timedelta(seconds=1)
        datafile2.save()
        out = StringIO()
        try:
            call_command('archive', experiment.id, location='archtest',
                         incremental=True, verbosity=1, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(), 
            'Archived experiment %s to %s%s-2-archive.tar.gz\n'
            'Archived 1 experiments with 0 errors\n' %
            (experiment.id, archtest.provider.base_url, experiment.id))

        # Test 'minSize' and 'maxSize' handling
        out = StringIO()
        err = StringIO()
        try:
            call_command('archive', experiment.id, location='archtest',
                         maxSize='1k', verbosity=1, stdout=out, stderr=err)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(), 
            'Archived 0 experiments with 1 errors\n')
        err.seek(0)
        self.assertEquals(
            err.read(), 
            'Archiving failed for experiment 1 : ' 
            'Archive for experiment 1 is too big\n')

        out = StringIO()
        err = StringIO()
        try:
            call_command('archive', experiment.id, location='archtest',
                         minSize='1g', verbosity=1, stdout=out, stderr=err)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(), 
            'Archived 0 experiments with 1 errors\n')
        err.seek(0)
        self.assertEquals(
            err.read(), 
            'Archiving failed for experiment 1 : ' 
            'Archive for experiment 1 is too small\n')

        # And with --force
        out = StringIO()
        err = StringIO()
        try:
            call_command('archive', experiment.id, location='archtest',
                         minSize='1g', verbosity=1, force=True,
                         stdout=out, stderr=err)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(), 
            'Archived experiment %s to %s%s-3-archive.tar.gz\n'
            'Archived 1 experiments with 0 errors\n' % 
            (experiment.id, archtest.provider.base_url, experiment.id))
        err.seek(0)
        self.assertEquals(
            err.read(), 
            'Warning: archive for experiment 1 is too small\n')

        # Now test --keepOnly
        self.assertEquals(Archive.objects.count(), 3)
        out = StringIO()
        try:
            call_command('archive', experiment.id, location='archtest',
                         keepOnly=2, verbosity=1, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(), 
            'Archived experiment %s to %s%s-4-archive.tar.gz\n' \
                'Archived 1 experiments with 0 errors\n' % \
                (experiment.id, archtest.provider.base_url, 
                 experiment.id))
        self.assertEquals(Archive.objects.count(), 2)
        for a in Archive.objects.all():
            self.assertTrue(a.id in [3, 4])
        

