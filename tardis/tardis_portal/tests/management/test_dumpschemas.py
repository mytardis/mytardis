import json

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from ...models.parameters import Schema


class DumpSchemasTestCase(TestCase):
    def setUp(self):
        self.schema1 = Schema(
            namespace="http://www.example.com/schema1.xml", type=Schema.DATAFILE
        )
        self.schema1.save()
        self.schema2 = Schema(
            namespace="http://www.example.com/schema2.xml", type=Schema.DATAFILE
        )
        self.schema2.save()

    def testDumpSchemas(self):
        """
        Just test that we can run
        ./manage.py dumpschemas
        without any runtime exceptions
        """
        schemas = json.loads(
            call_command(
                "dumpschemas",
                "http://www.example.com/schema1.xml",
                "http://www.example.com/schema2.xml",
            )
        )
        self.assertEqual(len(schemas), 2)
        schemas = json.loads(
            call_command("dumpschemas", "http://www.example.com/schema1.xml")
        )
        self.assertEqual(len(schemas), 1)
        with self.assertRaises(CommandError):
            call_command("dumpschemas", "invalid")

    def tearDown(self):
        self.schema1.delete()
        self.schema2.delete()
