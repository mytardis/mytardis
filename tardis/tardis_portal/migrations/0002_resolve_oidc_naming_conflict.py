# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tardis_portal', '0001_squashed_0011_auto_20160505_1643'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='user',
            field=models.ForeignKey(related_name='mt_token', to=settings.AUTH_USER_MODEL),
        ),
    ]
