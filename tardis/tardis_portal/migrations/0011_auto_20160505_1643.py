# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tardis_portal", "0010_auto_20160503_1443"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datafile",
            name="directory",
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="dataset",
            name="directory",
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="experimentauthor",
            name="url",
            field=models.URLField(
                help_text=b"URL identifier for the author",
                max_length=255,
                null=True,
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="license",
            name="image_url",
            field=models.URLField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name="license",
            name="name",
            field=models.CharField(unique=True, max_length=255),
        ),
        migrations.AlterField(
            model_name="license",
            name="url",
            field=models.URLField(
                help_text=b"Link to document outlining licensing details.",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="storagebox",
            name="name",
            field=models.CharField(default=b"default", unique=True, max_length=255),
        ),
    ]
