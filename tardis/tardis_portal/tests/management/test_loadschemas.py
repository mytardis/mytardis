from django.core.management import call_command
from django.test import TestCase

from ...models.parameters import Schema


class LoadSchemasTestCase(TestCase):

    def testLoadSchemas(self):
        '''
        Test that we can run
        ./manage.py loadschemas tardis/tardis_portal/fixtures/jeol_metadata_schema.json
        '''
        schema_count = Schema.objects.count()
        call_command(
            'loadschemas',
            'tardis/tardis_portal/fixtures/jeol_metadata_schema.json')
        self.assertEqual(Schema.objects.count(), schema_count + 1)
