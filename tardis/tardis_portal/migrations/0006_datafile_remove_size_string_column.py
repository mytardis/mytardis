# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tardis_portal", "0005_datafile_add_size_int_column"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="datafile",
            name="size",
        ),
        migrations.RenameField(
            model_name="datafile",
            old_name="_size",
            new_name="size",
        ),
    ]
