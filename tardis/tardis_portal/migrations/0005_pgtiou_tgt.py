# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0004_storageboxoption_value_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='PgtIOU',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pgtIou', models.CharField(unique=True, max_length=255)),
                ('tgt', models.CharField(max_length=255)),
                ('created', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Tgt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(unique=True, max_length=255)),
                ('tgt', models.CharField(max_length=255)),
                ('created', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
