# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0002_auto_20150528_1128'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafileparameter',
            name='string_value',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='datasetparameter',
            name='string_value',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='experimentauthor',
            name='url',
            field=models.URLField(help_text=b'URL identifier for the author', max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='experimentparameter',
            name='string_value',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='instrumentparameter',
            name='string_value',
            field=models.CharField(max_length=255, null=True, blank=True),
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
            model_name='parametername',
            name='data_type',
            field=models.IntegerField(default=2, choices=[(1, b'NUMERIC'), (2, b'STRING'), (3, b'URL'), (4, b'LINK'), (5, b'FILENAME'), (6, b'DATETIME'), (7, b'LONGSTRING'), (8, b'JSON')]),
        ),
        migrations.AlterField(
            model_name='storagebox',
            name='name',
            field=models.CharField(default=b'default', unique=True, max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='datafile',
            unique_together=set([('dataset', 'filename', 'version')]),
        ),
    ]
