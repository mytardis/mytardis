# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tardis_portal", "0009_auto_20160128_1119"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datafile",
            name="mimetype",
            field=models.CharField(db_index=True, max_length=80, blank=True),
        ),
    ]
