# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0003_auto_20150907_1315'),
    ]

    operations = [
        migrations.AddField(
            model_name='storageboxoption',
            name='value_type',
            field=models.CharField(default=b'string', max_length=6, choices=[(b'string', b'String value'), (b'pickle', b'Pickled value')]),
        ),
    ]
