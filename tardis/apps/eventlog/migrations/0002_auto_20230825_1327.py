# Generated by Django 3.2.7 on 2023-08-25 03:27

import django.core.serializers.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventlog', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='log',
            options={'ordering': ['-timestamp']},
        ),
        migrations.AlterField(
            model_name='log',
            name='extra',
            field=models.JSONField(verbose_name=django.core.serializers.json.DjangoJSONEncoder),
        ),
    ]