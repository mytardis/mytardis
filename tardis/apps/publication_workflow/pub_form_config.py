# coding=utf-8
"""
Set up publication form schemas
"""

import logging

from django.conf import settings
from django.contrib.auth.models import User, Group
from tardis.tardis_portal.models import Schema, ParameterName
from . import default_settings

logger = logging.getLogger(__name__)


class PubFormConfig():

    def _setup_PUBLICATION_SCHEMA_ROOT(self, namespace):
        schema, _ = Schema.objects.get_or_create(namespace=namespace,
                                                 name='Publication',
                                                 hidden=True,
                                                 immutable=True)

        ParameterName.objects.get_or_create(schema=schema,
                                            name='embargo',
                                            full_name='embargo',
                                            data_type=ParameterName.DATETIME,
                                            immutable=True)
        ParameterName.objects.get_or_create(schema=schema,
                                            name='pdb-embargo',
                                            full_name='pdb-embargo',
                                            data_type=ParameterName.STRING,
                                            immutable=True)
        ParameterName.objects.get_or_create(schema=schema,
                                            name='pdb-last-sync',
                                            full_name='pdb-last-sync',
                                            data_type=ParameterName.DATETIME,
                                            immutable=True)
        ParameterName.objects.get_or_create(schema=schema,
                                            name='form_state',
                                            full_name='form_state',
                                            data_type=ParameterName.STRING,
                                            immutable=True)

    def _setup_PUBLICATION_DRAFT_SCHEMA(self, namespace):
        schema, _ = Schema.objects.get_or_create(namespace=namespace,
                                                 name='Draft Publication',
                                                 hidden=True,
                                                 immutable=True)

    def _setup_PUBLICATION_DETAILS_SCHEMA(self, namespace):
        schema, _ = Schema.objects.get_or_create(namespace=namespace,
                                                 name='Publication Details',
                                                 hidden=False,
                                                 immutable=True)

        ParameterName.objects.get_or_create(schema=schema,
                                            name='doi',
                                            full_name='DOI',
                                            data_type=ParameterName.STRING,
                                            immutable=True)
        ParameterName.objects.get_or_create(schema=schema,
                                            name='acknowledgements',
                                            full_name='Acknowledgements',
                                            data_type=ParameterName.STRING,
                                            immutable=True)

    def _setup_GENERIC_PUBLICATION_DATASET_SCHEMA(self, namespace):
        schema, _ = Schema.objects.get_or_create(namespace=namespace,
                                                 name='Dataset details',
                                                 hidden=False,
                                                 immutable=True)

        ParameterName.objects.get_or_create(schema=schema,
                                            name='dataset',
                                            full_name='Dataset',
                                            data_type=ParameterName.STRING,
                                            immutable=True)
        ParameterName.objects.get_or_create(schema=schema,
                                            name='description',
                                            full_name='Description',
                                            data_type=ParameterName.STRING,
                                            immutable=True)

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
            ('GENERIC_PUBLICATION_DATASET_SCHEMA',
             'Generic dataset publication schema')]

        recommended_settings = [('PUBLICATION_FORM_MAPPINGS', ''),
                                ('PUBLICATION_NOTIFICATION_SENDER_EMAIL', '')]
        for setting, description in (required_settings + required_schemas +
                                     recommended_settings):
            if not hasattr(settings, setting):
                logger.info(setting + ' setting not found. Using defaults'
                                      ' for now, but you might encounter problems'
                                      ' later! (%s)' % description)

        for schema, description in required_schemas:
            logger.info('Setting up schema: ' + schema)
            getattr(self, '_setup_' + schema)(
                getattr(settings, schema,
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
