# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def cast_string_to_integer(apps, schema_editor):
    DataFile = apps.get_model("tardis_portal", "DataFile")
    for df in DataFile.objects.all():
        df._size = long(df.size)
        df.save()


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0004_storageboxoption_value_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='datafile',
            name='_size',
            field=models.BigIntegerField(null=True, blank=True),
        ),
        migrations.RunPython(cast_string_to_integer),
    ]
