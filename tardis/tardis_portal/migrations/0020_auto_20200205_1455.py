# -*- coding: utf-8 -*-
# Generated by Django 1.11.26 on 2020-02-05 01:55
from __future__ import unicode_literals

from django.db import migrations, models
import tardis.tardis_portal.models.experiment


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0019_auto_20191219_1139'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='internal_id',
            field=models.CharField(default=tardis.tardis_portal.models.experiment.experiment_internal_id_default, max_length=400, unique=True),
        ),
        migrations.AddField(
            model_name='experiment',
            name='project_id',
            field=models.CharField(default='project_id_1', max_length=400),
            preserve_default=False,
        ),
    ]
