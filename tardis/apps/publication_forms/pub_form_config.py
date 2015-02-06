# coding=utf-8
"""
Set up publication form schemas
"""

import logging

from django.conf import settings
from django.db import DatabaseError
from django.contrib.auth.models import User, Group

from tardis.tardis_portal.models import Schema, ParameterName

import default_settings

logger = logging.getLogger(__name__)


class PubFormConfig():
    def _schema_exists(self, namespace):
        try:
            return Schema.objects.filter(namespace=namespace).exists()
        except DatabaseError as e:
            logger.error('Database error encountered while checking if '
                         'schema '+namespace+' exists')
            raise e

    def _setup_PUBLICATION_SCHEMA_ROOT(self, namespace):
        schema = Schema(namespace=namespace, name='Publication', hidden=True,
                        immutable=True)
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
                      immutable=True,
                      order=2).save()
        ParameterName(schema=schema,
                      name='pdb-last-sync',
                      full_name='pdb-last-sync',
                      data_type=ParameterName.DATETIME,
                      immutable=True,
                      order=3).save()
        ParameterName(schema=schema,
                      name='form_state',
                      full_name='form_state',
                      data_type=ParameterName.STRING,
                      immutable=True,
                      order=4).save()

    def _setup_PUBLICATION_DRAFT_SCHEMA(self, namespace):
        schema = Schema(namespace=namespace, name='Draft Publication',
                        hidden=True, immutable=True)
        schema.save()

    def _setup_PDB_PUBLICATION_SCHEMA_ROOT(self, namespace):
        schema = Schema(namespace=namespace, name='Protein Data Bank',
                        hidden=False, immutable=True)
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
        schema = Schema(namespace=namespace, name='Sequence Data',
                        hidden=False, immutable=True)
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
        schema = Schema(namespace=namespace, name='Citation', hidden=False,
                        immutable=True)
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

    def _setup_PUBLICATION_DETAILS_SCHEMA(self, namespace):
        schema = Schema(namespace=namespace, name='Publication Details',
                        hidden=False, immutable=True)
        schema.save()
        ParameterName(schema=schema,
                      name='doi',
                      full_name='DOI',
                      data_type=ParameterName.STRING,
                      immutable=True,
                      order=1).save()
        ParameterName(schema=schema,
                      name='acknowledgements',
                      full_name='Acknowledgements',
                      data_type=ParameterName.STRING,
                      immutable=True,
                      order=2).save()

    def _setup_MX_PUBLICATION_DATASET_SCHEMA(self, namespace):
        schema = Schema(namespace=namespace, name='MX dataset details',
                        hidden=False, immutable=True)
        schema.save()
        ParameterName(schema=schema,
                      name='dataset',
                      full_name='Dataset',
                      data_type=ParameterName.STRING,
                      immutable=True,
                      order=1).save()
        ParameterName(schema=schema,
                      name='description',
                      full_name='Description',
                      data_type=ParameterName.STRING,
                      immutable=True,
                      order=2).save()
        ParameterName(schema=schema,
                      name='additional-information',
                      full_name='Additional information',
                      data_type=ParameterName.STRING,
                      immutable=True,
                      order=3).save()

    def do_setup(self, force=False):
        logger.info('Checking for required django settings.')

        required_settings = [('PUBLICATION_OWNER_GROUP',
                              'All publications are owned by this group')]
        required_schemas = [
            ('PUBLICATION_SCHEMA_ROOT',
             'A hidden schema that contians data required to manage the '
             'publication'),
            ('PUBLICATION_DRAFT_SCHEMA',
             'Stores the form state and is deleted once the form is '
             'completed'),
            ('PUBLICATION_DETAILS_SCHEMA',
             'Contains standard bibliographic details, such as DOI and '
             'acknowledgements'),
            ('PDB_PUBLICATION_SCHEMA_ROOT',
             'Standard protein crystallographic parameters'),
            ('PDB_SEQUENCE_PUBLICATION_SCHEMA',
             'Protein sequence data that might repeat depending on how many '
             'entities are present'),
            ('PDB_CITATION_PUBLICATION_SCHEMA',
             'Citation data that is extracted from the PDB record'),
            ('MX_PUBLICATION_DATASET_SCHEMA',
             'Macromolecular crystallography dataset publication schema')]

        recommended_settings = [('PUBLICATION_FORM_MAPPINGS', ''),
                                ('PDB_REFRESH_INTERVAL', ''),
                                ('PUBLICATION_NOTIFICATION_SENDER_EMAIL', '')]
        for setting, description in (required_settings + required_schemas +
                                     recommended_settings):
            if not hasattr(settings, setting):
                logger.info(setting + ' setting not found. Using defaults'
                               ' for now, but you might encounter problems'
                               ' later! (%s)' % description)

        for schema, description in required_schemas:
            if self._schema_exists(getattr(settings, schema,
                                           getattr(default_settings, schema))):
                logger.info('Schema ' + schema + ' exists, skipping.')
            else:
                logger.info('Setting up schema: ' + schema)
                getattr(self, '_setup_' + schema)(getattr(settings, schema,
                                            getattr(default_settings, schema)))

        pub_group = getattr(settings, 'PUBLICATION_OWNER_GROUP',
                            'publication-admin')
        try:
            Group.objects.get(name=pub_group)
            logger.info('Publication owner group exists.')
        except Group.DoesNotExist:
            logger.info('Publication owner group doesnt, so creating.')
            pub_owner_group = Group(name=pub_group)
            pub_owner_group.save()
            logger.info('Publication owner group created. Adding all'
                        'superusers.')
            superusers = User.objects.filter(is_superuser=True)
            pub_owner_group.user_set.add(*superusers)

        logger.info('Publication form setup complete.')
