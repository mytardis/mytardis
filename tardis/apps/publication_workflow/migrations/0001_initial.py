# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import warnings

from django.conf import settings
from django.db import migrations
from django.db.utils import IntegrityError

from tardis.apps.publication_workflow import default_settings

from tardis.tardis_portal.models.parameters import Schema
from tardis.tardis_portal.models.parameters import ParameterName
from tardis.tardis_portal.models.license import License

LICENSES = [
    {
        "fields": {
            "name": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "url": "https:\/\/creativecommons.org\/licenses\/by\/4.0\/",
            "internal_description": "This licence lets others distribute, remix, tweak, and build upon your work, even commercially, as long as they credit you for the original creation. This is the most accommodating of licences offered under Creative Commons.",
            "image_url": "https:\/\/licensebuttons.net\/l\/by\/4.0\/88x31.png"
        }
    },
    {
        "fields": {
            "name": "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)",
            "url": "https:\/\/creativecommons.org\/licenses\/by-sa\/4.0\/",
            "internal_description": "This licence lets others remix, tweak, and build upon your work even for commercial purposes, as long as they credit you and licence their new creations under the identical terms.",
            "image_url": "https:\/\/licensebuttons.net\/l\/by-sa\/4.0\/88x31.png"
      }
    },
    {
        "fields": {
            "name": "Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)",
            "url": "https:\/\/creativecommons.org\/licenses\/by-nc\/4.0\/",
            "internal_description": "This licence lets others remix, tweak, and build upon your work non-commercially, and although their new works must also acknowledge you and be non-commercial, they don\u2019t have to licence their derivative works on the same terms.",
            "image_url": "https:\/\/licensebuttons.net\/l\/by-nc\/4.0\/88x31.png"
        }
    },
    {
        "fields": {
            "name": "Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0)",
            "url": "https:\/\/creativecommons.org\/licenses\/by-nd\/4.0\/",
            "internal_description": "This licence allows for redistribution, commercial and non-commercial, as long as it is passed along unchanged and in whole, with credit to you.",
            "image_url": "https:\/\/licensebuttons.net\/l\/by-nd\/4.0\/88x31.png"
        }
    },
    {
        "fields": {
            "name": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
            "url": "https:\/\/creativecommons.org\/licenses\/by-nc-sa\/4.0\/",
            "internal_description": "This licence lets others remix, tweak, and build upon your work non-commercially, as long as they credit you and licence their new creations under the identical terms.",
            "image_url": "https:\/\/licensebuttons.net\/l\/by-nc-sa\/4.0\/88x31.png"
        }
    },
    {
        "fields": {
            "name": "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)",
            "url": "https:\/\/creativecommons.org\/licenses\/by-nc-nd\/4.0\/",
            "internal_description": "This licence is the most restrictive Creative Commons licence, only allowing others to download your works and share them with others as long as they credit you, but they can\u2019t change them in any way or use them commercially.",
            "image_url": "https:\/\/licensebuttons.net\/l\/by-nc-nd\/4.0\/88x31.png"
        }
    }
]


def forwards_func(apps, schema_editor):
    create_metadata_schemas(apps, schema_editor)
    load_licenses(apps, schema_editor)


def reverse_func(apps, schema_editor):
    remove_metadata_schemas(apps, schema_editor)
    remove_licenses(apps, schema_editor)


def create_metadata_schemas(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    User = apps.get_model('auth', 'User')
    Group = apps.get_model('auth', 'Group')

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
    params['Retracted Publication'] = [
        dict(name='retracted',
             full_name='Retracted',
             data_type=ParameterName.DATETIME),
        dict(name='reason',
             full_name='reason',
             data_type=ParameterName.STRING)
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
            ('PUBLICATION_RETRACTED_SCHEMA', 'Retracted Publication'),
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
        Group.objects.using(db_alias).get(name=pub_group_name)
    except Group.DoesNotExist:
        pub_owner_group = Group.objects\
            .using(db_alias)\
            .create(name=pub_group_name)
        superusers = User.objects.using(db_alias).filter(is_superuser=True)
        pub_owner_group.user_set.add(*superusers)


def remove_metadata_schemas(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Group = apps.get_model('auth', 'Group')

    for setting_name, schema_name in [
            ('PUBLICATION_SCHEMA_ROOT', 'Publication'),
            ('PUBLICATION_DRAFT_SCHEMA', 'Draft Publication'),
            ('PUBLICATION_RETRACTED_SCHEMA', 'Retracted Publication'),
            ('PUBLICATION_DETAILS_SCHEMA', 'Publication Details'),
            ('GENERIC_PUBLICATION_DATASET_SCHEMA', 'Dataset Details')]:
        namespace = getattr(
            settings, setting_name, getattr(
                default_settings, setting_name))

        try:
            schema = Schema.objects.using(db_alias).get(
                namespace=namespace, name=schema_name)
            for parameter_name in ParameterName.objects.using(db_alias).filter(schema=schema):
                parameter_name.delete()
            schema.delete()
        except Schema.DoesNotExist:
            warnings.warn(
                "Didn't find schema to delete for namespace: %s"
                % namespace)

        try:
            pub_group_name = getattr(
                settings, 'PUBLICATION_ADMIN_GROUP', 'publication-admin')
            Group.objects.using(db_alias).get(name=pub_group_name).delete()
        except Group.DoesNotExist:
            warnings.warn(
                "Didn't find '%s' group to delete." % pub_group_name)


def load_licenses(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    for license in LICENSES:
        try:
            License.objects.using(db_alias).get_or_create(
                name=license['fields']['name'],
                url=license['fields']['url'],
                is_active=True,
                allows_distribution=True,
                internal_description=license['fields']['internal_description'],
                image_url=license['fields']['image_url'])
        except IntegrityError:
            warnings.warn(
                "License '%s' already exists in the database"
                % license['fields']['name'])


def remove_licenses(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    for license in LICENSES:
        try:
            License.objects.using(db_alias).get(
                name=license['fields']['name']).delete()
        except License.DoesNotExist:
            warnings.warn(
                "License '%s' was not found in the database"
                % license['fields']['name'])


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0011_auto_20160505_1643'),
        ('auth', '0008_alter_user_username_max_length')
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
            reverse_func
            )
    ]
