# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("push_to", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="credential",
            name="key_type",
            field=models.CharField(
                max_length=100, null=True, verbose_name=b"Key type", blank=True
            ),
        ),
        migrations.AlterField(
            model_name="remotehost",
            name="key_type",
            field=models.CharField(
                max_length=100, null=True, verbose_name=b"Key type", blank=True
            ),
        ),
    ]
