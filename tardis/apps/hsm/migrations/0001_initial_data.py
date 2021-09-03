# -*- coding: utf-8 -*-

"""Django migration to provide initial schema data for the
hsm app."""

from django.db import migrations
from ..default_settings import HSM_DATASET_NAMESPACE


def forward_func(apps, schema_editor):
    """Create HSM Schemas"""
    db_alias = schema_editor.connection.alias
    # Import virtual models from migration history rather than final MT model
    SCHEMA = apps.get_model("tardis_portal", "Schema")
    PARAMETERNAME = apps.get_model("tardis_portal", "ParameterName")

    ds_schema = SCHEMA.objects\
        .using(db_alias)\
        .create(namespace=HSM_DATASET_NAMESPACE,
                name="Online Status",
                type=2, #DATASET = 2, or someone really changed up Schema!
                immutable=True)

    param_name = PARAMETERNAME.objects\
        .using(db_alias)\
        .create(
            name="online_files",
            full_name="Online Files",
            data_type=2, #STRING = 2, or someone really changed up ParameterName!
            immutable=True,
            order=1,
            schema=ds_schema)

    param_name = PARAMETERNAME.objects\
        .using(db_alias)\
        .create(
            name="updated",
            full_name="Last Updated",
            data_type=6, #DATETIME = 6, or someone really changed up ParameterName!
            immutable=True,
            order=2,
            schema=ds_schema)


def reverse_func(apps, schema_editor):
    """Remove HSM Schemas"""
    db_alias = schema_editor.connection.alias
    # Import virtual models from migration history rather than final MT model
    SCHEMA = apps.get_model("tardis_portal", "Schema")
    PARAMETERNAME = apps.get_model("tardis_portal", "ParameterName")
    DATASETPARAMETER = apps.get_model("tardis_portal", "DatasetParameter")
    DATASETPARAMETERSET = apps.get_model("tardis_portal", "DatasetParameterSet")

    try:
        ds_schema = SCHEMA.objects.using(db_alias)\
            .get(namespace=HSM_DATASET_NAMESPACE)
    except SCHEMA.DoesNotExist:
        return

    DATASETPARAMETERSET.objects\
        .using(db_alias)\
        .filter(schema=ds_schema).delete()

    param_names = PARAMETERNAME.objects.using(db_alias)\
        .filter(schema=ds_schema)

    for pn in param_names:
        DATASETPARAMETER.objects\
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
