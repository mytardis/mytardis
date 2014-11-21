# coding=utf-8
"""
Set up publication form schemas
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DatabaseError

from tardis.tardis_portal.models import Schema, ParameterName


class Command(BaseCommand):

    def _schema_exists(self, namespace):
        try:
            return Schema.objects.filter(namespace=namespace).exists()
        except DatabaseError as e:
            self.stdout.write('Database error encountered!')
            self.stdout.write('Make sure to run from tardis root (e.g. ./bin/django create_pub_schemas) and ensure your database is properly configured')
            raise e

    def _setup_PUBLICATION_SCHEMA_ROOT(self, namespace):
        schema = Schema(namespace=namespace, name='Publication', hidden=True, immutable=True)
        schema.save()
        ParameterName(schema=schema,
                      name='embargo',
                      full_name='embargo',
                      data_type=ParameterName.DATETIME,
                      immutable=True,
                      order=1).save()
        ParameterName(schema=schema,
                      name='pdb-embargo',
                      full_name='pdb-embargo',
                      data_type=ParameterName.STRING,
                      order=1).save()
        ParameterName(schema=schema,
                      name='pdb-last-sync',
                      full_name='pdb-last-sync',
                      data_type=ParameterName.DATETIME,
                      order=1).save()
        

    def _setup_PUBLICATION_DRAFT_SCHEMA(self, namespace):
        schema = Schema(namespace=namespace, name='Draft Publication', hidden=True, immutable=True)
        schema.save()
        ParameterName(schema=schema,
                      name='form_state',
                      full_name='form_state',
                      data_type=ParameterName.STRING,
                      immutable=True,
                      order=1).save()

    def _setup_PDB_PUBLICATION_SCHEMA_ROOT(self, namespace):
        schema = Schema(namespace=namespace, name='Protein Data Bank', hidden=False, immutable=True)
        schema.save()
        ParameterName(schema=schema,
                      name='pdb-id',
                      full_name='PDB ID',
                      data_type=ParameterName.STRING,
                      is_searchable=True,
                      immutable=True,
                      order=1).save()
        ParameterName(schema=schema,
                      name='url',
                      full_name='URL',
                      data_type=ParameterName.URL,
                      immutable=True,
                      order=2).save()
        ParameterName(schema=schema,
                      name='resolution',
                      full_name='Resolution',
                      units='Å',
                      data_type=ParameterName.NUMERIC,
                      is_searchable=True,
                      immutable=True,
                      order=3).save()
        ParameterName(schema=schema,
                      name='r-value',
                      full_name='R-Value',
                      units='(obs.)',
                      data_type=ParameterName.NUMERIC,
                      is_searchable=True,
                      immutable=True,
                      order=4).save()
        ParameterName(schema=schema,
                      name='r-free',
                      full_name='R-Free',
                      data_type=ParameterName.NUMERIC,
                      is_searchable=True,
                      immutable=True,
                      order=5).save()
        ParameterName(schema=schema,
                      name='space-group',
                      full_name='Space Group',
                      data_type=ParameterName.STRING,
                      is_searchable=True,
                      immutable=True,
                      order=6).save()
        ParameterName(schema=schema,
                      name='unit-cell',
                      full_name='Unit Cell (Å,°)',
                      data_type=ParameterName.STRING,
                      immutable=True,
                      order=7).save()

    def _setup_PDB_SEQUENCE_PUBLICATION_SCHEMA(self, namespace):
        schema = Schema(namespace=namespace, name='Sequence Data', hidden=False, immutable=True)
        schema.save()
        ParameterName(schema=schema,
                      name='expression-system',
                      full_name='Expression System',
                      data_type=ParameterName.STRING,
                      is_searchable=True,
                      immutable=True,
                      order=1).save()
        ParameterName(schema=schema,
                      name='organism',
                      full_name='Organism',
                      data_type=ParameterName.STRING,
                      is_searchable=True,
                      immutable=True,
                      order=2).save()
        ParameterName(schema=schema,
                      name='sequence',
                      full_name='Sequence',
                      data_type=ParameterName.STRING,
                      is_searchable=True,
                      immutable=True,
                      order=3).save()

    def _setup_PDB_CITATION_PUBLICATION_SCHEMA(self, namespace):
        schema = Schema(namespace=namespace, name='Citation', hidden=False, immutable=True)
        schema.save()
        ParameterName(schema=schema,
                      name='title',
                      full_name='Title',
                      data_type=ParameterName.STRING,
                      immutable=True,
                      order=1).save()
        ParameterName(schema=schema,
                      name='authors',
                      full_name='Authors',
                      data_type=ParameterName.STRING,
                      immutable=True,
                      order=2).save()
        ParameterName(schema=schema,
                      name='journal',
                      full_name='Journal',
                      data_type=ParameterName.STRING,
                      immutable=True,
                      order=3).save()
        ParameterName(schema=schema,
                      name='volume',
                      full_name='Volume',
                      data_type=ParameterName.STRING,
                      immutable=True,
                      order=4).save()
        ParameterName(schema=schema,
                      name='page-range',
                      full_name='Pages',
                      data_type=ParameterName.STRING,
                      immutable=True,
                      order=5).save()
        ParameterName(schema=schema,
                      name='doi',
                      full_name='DOI',
                      data_type=ParameterName.URL,
                      immutable=True,
                      order=6).save()
        
    def handle(self, *args, **options):
        self.stdout.write('Checking for required django settings...')

        settings_ok = True
        required_schemas = ['PUBLICATION_SCHEMA_ROOT',
                            'PUBLICATION_DRAFT_SCHEMA',
                            'PDB_PUBLICATION_SCHEMA_ROOT',
                            'PDB_SEQUENCE_PUBLICATION_SCHEMA',
                            'PDB_CITATION_PUBLICATION_SCHEMA']
        
        for setting in required_schemas:
            if not hasattr(settings, setting):
                self.stdout.write('* Could not find setting: '+setting)
                settings_ok = False

                if not settings_ok:
                    raise CommandError('All required settings not present. Aborting!')
        
        self.stdout.write("All settings seem OK.")

        recommended_settings = ['PUBLICATION_FORM_MAPPINGS',
                                'PDB_REFRESH_INTERVAL']
        for setting in recommended_settings:
            if not hasattr(settings, setting):
                self.stdout.write('Warning: '+setting+' setting not found. You might encounter problems later!')

        self.stdout.write('Setting up schemas...')

        for schema in required_schemas:
            if self._schema_exists(getattr(settings, schema)):
                self.stdout.write('Schema '+schema+' exists, skipping.')
            else:
                self.stdout.write('Setting up '+schema+'... ', ending='')
                getattr(self,'_setup_'+schema)(getattr(settings, schema))
                self.stdout.write('Done.')

        self.stdout.write('Setup complete.')
