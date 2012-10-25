import os
from StringIO import StringIO

from django.test import TestCase
from django.test.client import Client
from django.core.management import call_command

from tardis.test_settings import FILE_STORE_PATH

from tardis.apps.migration.tests import SimpleHttpTestServer
from tardis.tardis_portal.models import Dataset_File, Dataset, Experiment

class MigrateCommandTestCase(TestCase):

    def setUp(self):
        self.dummy_dataset = Dataset()
        self.dummy_dataset.save()
        self.server = SimpleHttpTestServer()
        self.server.start()

    def tearDown(self):
        self.dummy_dataset.delete()
        self.server.stop()

    def testMigrateDataset(self):
        datafile = self._generate_datafile("1/2/3", "Hi mum")
        err = StringIO()
        call_command('migrate', 'datafile', datafile.id, stderr=err)
        err.seek(0)
        self.assertEquals(err.read(), 
                          'Migration failed for datafile %s : ' \
                          'Only verified datafiles can be migrated ' \
                          'to this destination\n' % datafile.id)
                          
        err = StringIO()
        call_command('migrate', 'datafile', 999, stderr=err)
        err.seek(0)
        self.assertEquals(err.read(), 'Datafile 999 does not exist\n')

    def _generate_datafile(self, path, content):
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
        datafile.save()
        return datafile

