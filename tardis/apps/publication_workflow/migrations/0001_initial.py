# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import warnings

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import migrations

from tardis.apps.publication_workflow import default_settings

from tardis.tardis_portal.models.parameters import ParameterName
from tardis.tardis_portal.models.parameters import Schema


def create_metadata_schemas(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    params = dict()
    params['Publication'] = [
        dict(name='embargo',
             full_name='embargo',
             data_type=ParameterName.DATETIME),
        dict(name='form_state',
             full_name='form_state',
             data_type=ParameterName.STRING)
    ]
    params['Draft Publication'] = [
    ]
    params['Publication Details'] = [
        dict(name='doi',
             full_name='DOI',
             data_type=ParameterName.STRING),
        dict(name='acknowledgements',
             full_name='Acknowledgements',
             data_type=ParameterName.STRING)
    ]
    params['Dataset Details'] = [
        dict(name='dataset',
             full_name='Dataset',
             data_type=ParameterName.STRING),
        dict(name='description',
             full_name='Description',
             data_type=ParameterName.STRING)
    ]

    schemas = dict()
    for setting_name, schema_name in [
            ('PUBLICATION_SCHEMA_ROOT', 'Publication'),
            ('PUBLICATION_DRAFT_SCHEMA', 'Draft Publication'),
            ('PUBLICATION_DETAILS_SCHEMA', 'Publication Details'),
            ('GENERIC_PUBLICATION_DATASET_SCHEMA', 'Dataset Details')]:
        namespace = getattr(
            settings, setting_name, getattr(
                default_settings, setting_name))
        try:
            schemas[schema_name] = Schema.objects\
                .using(db_alias)\
                .get(
                    namespace=namespace,
                    name=schema_name,
                    hidden=True,
                    immutable=True)
        except Schema.DoesNotExist:
            schemas[schema_name] = Schema.objects\
                .using(db_alias)\
                .create(
                    namespace=namespace,
                    name=schema_name,
                    hidden=True,
                    immutable=True)

        for param in params[schema_name]:
            ParameterName.objects\
                .using(db_alias)\
                .get_or_create(
                    schema=schemas[schema_name],
                    name=param['name'],
                    full_name=param['full_name'],
                    data_type=param['data_type'],
                    immutable=True)

    pub_group_name = getattr(
        settings, 'PUBLICATION_ADMIN_GROUP', 'publication-admin')
    try:
        Group.objects\
            .using(db_alias)\
            .get(name=pub_group_name)
    except Group.DoesNotExist:
        pub_owner_group = Group.objects\
            .using(db_alias)\
            .create(name=pub_group_name)
        superusers = User.objects\
            .using(db_alias)\
            .filter(is_superuser=True)
        pub_owner_group.user_set.add(*superusers)


def remove_metadata_schemas(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Schema = apps.get_model('tardis_portal', 'Schema')

    for setting_name, schema_name in [
            ('PUBLICATION_SCHEMA_ROOT', 'Publication'),
            ('PUBLICATION_DRAFT_SCHEMA', 'Draft Publication'),
            ('PUBLICATION_DETAILS_SCHEMA', 'Publication Details'),
            ('GENERIC_PUBLICATION_DATASET_SCHEMA', 'Dataset Details')]:
        namespace = getattr(
            settings, setting_name, getattr(
                default_settings, setting_name))
        try:
            Schema.objects\
                .using(db_alias)\
                .get(namespace=namespace, name=schema_name)\
                .delete()
        except Schema.DoesNotExist:
            warnings.warn(
                "Didn't find schema to delete for namespace: %s"
                % namespace)

        try:
            pub_group_name = getattr(
                settings, 'PUBLICATION_ADMIN_GROUP', 'publication-admin')
            Group.objects.get(name=pub_group_name).delete()
        except Group.DoesNotExist:
            warnings.warn(
                "Didn't find '%s' group to delete." % pub_group_name)


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0011_auto_20160505_1643'),
    ]

    operations = [
        migrations.RunPython(
            create_metadata_schemas,
            remove_metadata_schemas
            )
    ]
