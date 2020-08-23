'''
Tests for HSM app's migrations
'''
from unittest import skip

from django.db.migrations.executor import MigrationExecutor
from django.db import connections, DEFAULT_DB_ALIAS
from django.test import TestCase


class HsmAppMigrationTestCase(TestCase):
    @skip
    def test_migration(self):
        '''
        Test unapplying and reapplying the migration which creates
        the metadata for the HSM app
        '''
        from tardis.tardis_portal.models.parameters import Schema

        connection = connections[DEFAULT_DB_ALIAS]
        executor = MigrationExecutor(connection.constraint_checks_disabled())

        executor.migrate([("hsm", None)])
        executor.loader.build_graph()

        schema = Schema.objects.filter(
            namespace='http://mytardis.org/schemas/hsm/dataset/1').first()
        self.assertIsNone(schema)

        executor.migrate([("hsm", "0001_initial_data")])
        executor.loader.build_graph()

        schema = Schema.objects.filter(
            namespace='http://mytardis.org/schemas/hsm/dataset/1').first()
        self.assertIsNotNone(schema)
