# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tardis_portal", "0006_datafile_remove_size_string_column"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datafileparameter",
            name="string_value",
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="datasetparameter",
            name="string_value",
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="experimentparameter",
            name="string_value",
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="instrumentparameter",
            name="string_value",
            field=models.TextField(null=True, blank=True),
        ),
    ]
