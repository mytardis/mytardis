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

import os
from datetime import datetime
from StringIO import StringIO

from django.test import TestCase
from django.test.client import Client
from django.core.management import call_command
from django.core.management.base import CommandError

from django.conf import settings
from tardis.test_settings import FILE_STORE_PATH

from tardis.tardis_portal.tests.transfer.generate import \
    generate_datafile, generate_dataset, generate_experiment, \
    generate_user
from tardis.apps.migration.models import Archive
from tardis.apps.migration.management.commands.archivelist import Command


class ArchiveCommandTestCase(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testArchiveListGetdate(self):
        cmd = Command()
        self.assertTrue(cmd._get_datetime({'foo': '2007-07-07'}, 
                                          'foo'))
        self.assertTrue(cmd._get_datetime({'foo': '2007-07-07T01:01:01'}, 
                                          'foo'))
        self.assertFalse(cmd._get_datetime({'foo': '2007-07-07'}, 
                                          'bar'))
        self.assertTrue(cmd._get_datetime({'foo': '2007-07-07'}, 'foo') <
                        cmd._get_datetime({'foo': '2007-07-08'}, 'foo'))
        self.assertTrue(cmd._get_datetime({'foo': '2007-07-07'}, 
                                          'foo', end=True) <
                        cmd._get_datetime({'foo': '2007-07-08'}, 'foo'))
        self.assertTrue(cmd._get_datetime({'foo': '2007-07-07'}, 
                                          'foo', end=True) >
                        cmd._get_datetime({'foo': '2007-07-07'}, 'foo'))

    def testArchiveList(self):
        user = generate_user('bert')
        dataset = generate_dataset()
        experiment = generate_experiment([dataset], [user])

        Archive(experiment=experiment, 
                experiment_owner='bert', 
                experiment_title='cheese',
                experiment_changed=datetime(year=2001,month=1,day=1,
                                            hour=1,minute=1,second=1),
                archive_url="http://example.com/archive-1",
                nos_files=0, nos_errors=0, size=0).save()

        out = StringIO()
        try:
            call_command('archivelist', count=True, stdout=out)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(),
            "There are 1 archives meeting the selection criteria\n")

        # Selection by user
        out = StringIO()
        try:
            call_command('archivelist', count=True, stdout=out, user='bert')
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(),
            "There are 1 archives meeting the selection criteria\n")
        out = StringIO()
        try:
            call_command('archivelist', count=True, stdout=out, user='joe')
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(),
            "There are 0 archives meeting the selection criteria\n")

        # Selection by user and title
        out = StringIO()
        try:
            call_command('archivelist', count=True, stdout=out, 
                         user='bert', title='cheese')
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(),
            "There are 1 archives meeting the selection criteria\n")
        out = StringIO()
        try:
            call_command('archivelist', count=True, stdout=out, 
                         user='bert', title='crackers')
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(),
            "There are 0 archives meeting the selection criteria\n")

        # Selection by date
        out = StringIO()
        try:
            call_command('archivelist', count=True, stdout=out, 
                         date='2001-01-01', experimentDate=True)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(),
            "There are 1 archives meeting the selection criteria\n")
        out = StringIO()
        try:
            call_command('archivelist', count=True, stdout=out, 
                         date='2001-01-02', experimentDate=True)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(),
            "There are 0 archives meeting the selection criteria\n")

        # Now print them:
        out = StringIO()
        try:
            call_command('archivelist', count=False, stdout=out, 
                         date='2001-01-01', experimentDate=True)
        except SystemExit:
            pass
        out.seek(0)
        self.assertEquals(
            out.read(),
            "1 : bert : 2001-01-01 01:01:01 : http://example.com/archive-1\n")

        
