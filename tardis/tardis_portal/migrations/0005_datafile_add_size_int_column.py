# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django.db import migrations, models


def cast_string_to_integer(apps, schema_editor):
    DataFile = apps.get_model("tardis_portal", "DataFile")
    total_objects = DataFile.objects.all().count()

    print()
    current_object = 0
    for df in DataFile.objects.all().iterator():
        df._size = int(df.size)
        df.save()
        current_object += 1
        if current_object % 10000 == 0:
            print(
                "{0} of {1} datafile objects converted".format(
                    current_object, total_objects
                )
            )


class Migration(migrations.Migration):

    dependencies = [
        ("tardis_portal", "0004_storageboxoption_value_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="datafile",
            name="_size",
            field=models.BigIntegerField(null=True, blank=True),
        ),
        migrations.RunPython(cast_string_to_integer),
    ]
