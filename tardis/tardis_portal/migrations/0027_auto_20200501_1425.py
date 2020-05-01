# Generated by Django 2.2.10 on 2020-05-01 02:25

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0011_update_proxy_permissions'),
        ('tardis_portal', '0026_auto_20200331_1634'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='experiment',
            name='institution_name',
        ),
        migrations.RemoveField(
            model_name='project',
            name='contact',
        ),
        migrations.RemoveField(
            model_name='project',
            name='member',
        ),
        migrations.RemoveField(
            model_name='project',
            name='owner',
        ),
        migrations.AddField(
            model_name='facility',
            name='url',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='lead_researcher',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='project',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 5, 1, 2, 25, 35, 770837)),
        ),
        migrations.AddField(
            model_name='project',
            name='url',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='The University of Auckland', max_length=255)),
                ('ror', models.CharField(blank=True, default='https://ror.org/03b94tp07', max_length=100, null=True)),
                ('url', models.URLField(blank=True, default='https://auckland.ac.nz', max_length=255, null=True)),
                ('manager_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.Group')),
            ],
        ),
        migrations.AddField(
            model_name='project',
            name='institution',
            field=models.ManyToManyField(related_name='institutions', to='tardis_portal.Institution'),
        ),
    ]
