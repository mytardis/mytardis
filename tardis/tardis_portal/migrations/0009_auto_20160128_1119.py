# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tardis_portal", "0008_string_value_partial_index_postgres"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="instrument",
            unique_together=set([("name", "facility")]),
        ),
    ]
