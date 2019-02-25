# -*- coding: utf-8 -*-

"""Django migration to provide initial schema data for the
hsm app."""

from django.db import migrations
from tardis.tardis_portal.models import (Schema, ParameterName,
                                         DatasetParameter, DatasetParameterSet)
from ..default_settings import HSM_DATASET_NAMESPACE


def forward_func(apps, schema_editor):
    """Create HSM Schemas"""
    db_alias = schema_editor.connection.alias
    ds_schema = Schema.objects\
        .using(db_alias)\
        .create(namespace=HSM_DATASET_NAMESPACE,
                name="Online Status",
                type=Schema.DATASET,
                immutable=True)

    param_name = ParameterName.objects\
        .using(db_alias)\
        .create(
            name="online_files",
            full_name="Online Files",
            data_type=ParameterName.STRING,
            immutable=True,
            order=1,
            schema=ds_schema)

    param_name = ParameterName.objects\
        .using(db_alias)\
        .create(
            name="updated",
            full_name="Last Updated",
            data_type=ParameterName.DATETIME,
            immutable=True,
            order=2,
            schema=ds_schema)


def reverse_func(apps, schema_editor):
    """Remove HSM Schemas"""
    db_alias = schema_editor.connection.alias

    try:
        ds_schema = Schema.objects.using(db_alias)\
            .get(namespace=HSM_DATASET_NAMESPACE)
    except Schema.DoesNotExist:
        return

    DatasetParameterSet.objects\
        .using(db_alias)\
        .filter(schema=ds_schema).delete()

    param_names = ParameterName.objects.using(db_alias)\
        .filter(schema=ds_schema)

    for pn in param_names:
        DatasetParameter.objects\
            .using(db_alias)\
            .filter(name=pn).delete()
        pn.delete()

    ds_schema.delete()


class Migration(migrations.Migration):
    """HSM Schema migrations"""
    dependencies = [
        ("tardis_portal", "0016_add_timestamps"),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_func),
    ]
