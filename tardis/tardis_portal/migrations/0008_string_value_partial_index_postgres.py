# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations, connection
from tardis.tardis_portal.models import ExperimentParameter, DatasetParameter, \
    DatafileParameter, InstrumentParameter
from tardis import settings

def _generate_index_migrations():
    max_length = 256

    # if 'postgres' not in settings.DATABASES['default']['ENGINE'].lower():
    #     return []
    if hasattr(connection, 'vendor') and 'postgresql' not in connection.vendor:
        return []

    string_value_tables = [
        ExperimentParameter.objects.model._meta.db_table,
        DatasetParameter.objects.model._meta.db_table,
        DatafileParameter.objects.model._meta.db_table,
        InstrumentParameter.objects.model._meta.db_table,
    ]

    create_template = "CREATE INDEX %s ON %s(string_value) " \
                      "WHERE char_length(string_value) <= %s;"

    operations = []
    for table_name in string_value_tables:
        index_name = table_name + "_string_value"
        ops = [
            migrations.RunSQL(
             "DROP INDEX IF EXISTS %s;" % index_name,
             reverse_sql=create_template % (index_name, table_name, max_length)
            ),
            migrations.RunSQL(
             create_template % (index_name, table_name, max_length),
             reverse_sql="DROP INDEX IF EXISTS %s;" % index_name
            ),
        ]

        operations.extend(ops)

    return operations


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0007_remove_parameter_string_value_index'),
    ]

    operations = _generate_index_migrations()
