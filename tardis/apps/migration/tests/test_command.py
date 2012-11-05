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
from tardis.tardis_portal.models import \
    Dataset_File, Dataset, Experiment, UserProfile

class MigrateCommandTestCase(TestCase):

    def setUp(self):
        self.dummy_dataset = Dataset()
        self.dummy_dataset.save()
        self.dummy_user = self._generate_user()
        self.server = SimpleHttpTestServer()
        self.server.start()

    def tearDown(self):
        self.dummy_dataset.delete()
        self.dummy_user.delete()
        self.server.stop()

    def testMigrateDatafile(self):
        datafile = self._generate_datafile("1/2/3", "Hi mum", verify=False)
        datafile2 = self._generate_datafile("1/2/4", "Hi mum")
        datafile3 = self._generate_datafile("1/2/5", "Hi mum")
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
        err = StringIO()
        try:
            call_command('migratefiles', 'datafile', datafile.id, 
                         verbosity=2, stderr=err)
        except SystemExit:
            pass
        err.seek(0)
        self.assertEquals(err.read(), 
                          'Migrated datafile %s\n' % datafile.id)

        err = StringIO()
        try:
            call_command('migratefiles', 'datafile', datafile2.id, datafile3.id, 
                         verbosity=1, stderr=err)
        except SystemExit:
            pass
        err.seek(0)
        self.assertEquals(err.read(), '') 

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
        datafile = self._generate_datafile("2/2/3", "Hi mum")
        datafile2 = self._generate_datafile("2/2/4", "Hi mum")
        datafile3 = self._generate_datafile("2/2/5", "Hi mum")
        dataset = self._generate_dataset([datafile,datafile2,datafile3])

        err = StringIO()
        try:
            call_command('migratefiles', 'dataset', dataset.id, 
                         verbosity=2, stderr=err)
        except SystemExit:
            pass
        err.seek(0)
        self.assertEquals(err.read(), 
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n'
                          'Migrated datafile %s\n' % 
                          (datafile.id, datafile2.id, datafile3.id))

    def testMigrateExperiment(self):
        datafile = self._generate_datafile("3/2/3", "Hi mum")
        datafile2 = self._generate_datafile("3/2/4", "Hi mum")
        datafile3 = self._generate_datafile("3/2/5", "Hi mum")
        dataset = self._generate_dataset([datafile,datafile2,datafile3])
        experiment = self._generate_experiment([dataset])

        err = StringIO()
        try:
            call_command('migratefiles', 'experiment', experiment.id, 
                         verbosity=2, stderr=err)
        except SystemExit:
            pass
        err.seek(0)
        self.assertEquals(err.read(), 
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

    def _generate_datafile(self, path, content, verify=True):
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
        datafile.filename = os.path.basename(filepath)
        datafile.dataset_id = self.dummy_dataset.id
        datafile.size = str(len(content))
        if verify:
            self.assertEquals(datafile.verify(allowEmptyChecksums=True), True)
        datafile.save()
        return datafile

    def _generate_dataset(self, datafiles):
        dataset = Dataset()
        dataset.save()
        for df in datafiles:
            df.dataset_id = dataset.id
            df.save()
        return dataset

    def _generate_experiment(self, datasets):
        experiment = Experiment(created_by=self.dummy_user)
        experiment.save()
        for ds in datasets:
            ds.experiments.add(experiment)
            ds.save()
        return experiment

    def _generate_user(self):
        user = User(username='jim',
                    first_name='James',
                    last_name='Spriggs',
                    email='jim.spriggs@goonshow.com')
        user.save()
        UserProfile(user=user).save()
        return user
