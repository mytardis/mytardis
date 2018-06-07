from django.test import TestCase
from django.core.management import call_command

from tardis.tardis_portal.models.parameters import Schema


class LoadSchemasTestCase(TestCase):

    def testLoadSchemas(self):
        '''
        Test that we can run
        ./mytardis.py loadschemas tardis/tardis_portal/fixtures/jeol_metadata_schema.json
        '''
        self.assertEqual(Schema.objects.count(), 0)
        call_command(
            'loadschemas',
            'tardis/tardis_portal/fixtures/jeol_metadata_schema.json')
        self.assertEqual(Schema.objects.count(), 1)
