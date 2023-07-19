# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('push_to', '0002_auto_20160518_1953'),
    ]

    operations = [
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('object_type', models.CharField(max_length=10)),
                ('object_id', models.PositiveIntegerField()),
                ('base_dir', models.CharField(max_length=100, null=True)),
                ('message', models.CharField(max_length=100, null=True)),
                ('credential', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='push_to.Credential')),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='push_to.RemoteHost')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Progress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.PositiveIntegerField(default=0)),
                ('message', models.CharField(max_length=100, null=True)),
                ('retry', models.PositiveIntegerField(default=0)),
                ('timestamp', models.DateTimeField(null=True)),
                ('datafile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tardis_portal.DataFile')),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='push_to.Request')),
            ],
        ),
    ]
