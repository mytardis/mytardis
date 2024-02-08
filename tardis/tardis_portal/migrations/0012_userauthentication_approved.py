# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tardis_portal", "0011_auto_20160505_1643"),
    ]

    operations = [
        migrations.AddField(
            model_name="userauthentication",
            name="approved",
            field=models.BooleanField(default=True),
        ),
    ]
