from django.test import TestCase
from django.core.management import call_command

from tardis.tardis_portal.models.parameters import Schema


class DumpSchemasTestCase(TestCase):

    def setUp(self):
        self.schema = Schema(
            namespace='http://www.example.com/schema1.xml',
            type=Schema.DATAFILE)
        self.schema.save()

    def testDumpSchemas(self):
        '''
        Just test that we can run
        ./mytardis.py dumpschemas
        without any runtime exceptions
        '''
        call_command('dumpschemas')
        call_command('dumpschemas', namespaces=['http://www.example.com/schema1.xml'])

    def tearDown(self):
        self.schema.delete()
