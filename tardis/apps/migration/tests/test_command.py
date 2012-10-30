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
            call_command('migrate', 'datafile', datafile.id, stderr=err)
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
            call_command('migrate', 'datafile', datafile.id, 
                         verbosity=2, stderr=err)
        except SystemExit:
            pass
        err.seek(0)
        self.assertEquals(err.read(), 
                          'Migrated datafile %s\n' % datafile.id)

        err = StringIO()
        try:
            call_command('migrate', 'datafile', datafile2.id, datafile3.id, 
                         verbosity=1, stderr=err)
        except SystemExit:
            pass
        err.seek(0)
        self.assertEquals(err.read(), '') 

        err = StringIO()
        try:
            call_command('migrate', 'datafile', datafile.id, 
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
            call_command('migrate', 'dataset', dataset.id, 
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
            call_command('migrate', 'experiment', experiment.id, 
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
            call_command('migrate', 'datafile', 999, stderr=err)
        except SystemExit:
            pass
        err.seek(0)
        self.assertEquals(err.read(), 'Datafile 999 does not exist\n')

        err = StringIO()
        try:
            call_command('migrate', 'datafile', 999, dest='nowhere', stderr=err)
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
                call_command('migrate', 'datafile', 999, stderr=err)
            except SystemExit:
                pass
            err.seek(0)
            self.assertEquals(err.read(), 
                              'Error: No default destination has been ' \
                                  'configured\n')
        finally:
            settings.DEFAULT_MIGRATION_DESTINATION = saved

        try:
            saved = settings.MIGRATION_DESTINATIONS
            settings.MIGRATION_DESTINATIONS = []
            err = StringIO()
            try:
                call_command('migrate', 'datafile', 999, stderr=err)
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
        datafile.filename = filepath
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
