# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0002_auto_20150528_1128'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parametername',
            name='data_type',
            field=models.IntegerField(default=2, choices=[(1, b'NUMERIC'), (2, b'STRING'), (3, b'URL'), (4, b'LINK'), (5, b'FILENAME'), (6, b'DATETIME'), (7, b'LONGSTRING'), (8, b'JSON')]),
        ),
    ]
