# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tardis.tardis_portal.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0004_storageboxoption_value_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafile',
            name='directory',
            field=tardis.tardis_portal.models.fields.DirectoryField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='datafileparameter',
            name='string_value',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='directory',
            field=tardis.tardis_portal.models.fields.DirectoryField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='datasetparameter',
            name='string_value',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='experimentauthor',
            name='url',
            field=models.URLField(help_text=b'URL identifier for the author', max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='experimentparameter',
            name='string_value',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='instrumentparameter',
            name='string_value',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='license',
            name='image_url',
            field=models.URLField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='license',
            name='name',
            field=models.CharField(unique=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='license',
            name='url',
            field=models.URLField(help_text=b'Link to document outlining licensing details.', unique=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='storagebox',
            name='name',
            field=models.CharField(default=b'default', unique=True, max_length=255),
        ),
    ]
