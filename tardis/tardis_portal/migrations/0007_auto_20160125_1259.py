# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0006_datafile_remove_size_string_column'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instrument',
            name='name',
            field=models.CharField(unique=True, max_length=100),
        ),
    ]
