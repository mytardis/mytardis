# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0002_auto_20150528_1128'),
    ]

    operations = [
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(unique=True, max_length=30)),
                ('description', models.TextField(blank=True)),
                ('make', models.CharField(max_length=60, blank=True)),
                ('model', models.CharField(max_length=60, blank=True)),
                ('type', models.CharField(max_length=60, blank=True)),
                ('serial', models.CharField(max_length=60, blank=True)),
                ('comm', models.DateField(null=True, blank=True)),
                ('decomm', models.DateField(null=True, blank=True)),
                ('url', models.URLField(max_length=255, null=True, blank=True)),
                ('dataset', models.ManyToManyField(to='tardis_portal.Dataset', null=True, blank=True)),
            ],
        ),
    ]
