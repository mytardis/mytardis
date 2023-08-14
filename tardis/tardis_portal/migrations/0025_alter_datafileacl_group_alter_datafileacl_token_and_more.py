# Generated by Django 4.2.2 on 2023-08-02 04:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tardis_portal", "0024_auto_20220307_1638"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datafileacl",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)ss",
                to="auth.group",
            ),
        ),
        migrations.AlterField(
            model_name="datafileacl",
            name="token",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)ss",
                to="tardis_portal.token",
            ),
        ),
        migrations.AlterField(
            model_name="datafileacl",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)ss",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="datafileparameterset",
            name="storage_box",
            field=models.ManyToManyField(
                related_name="%(class)ss", to="tardis_portal.storagebox"
            ),
        ),
        migrations.AlterField(
            model_name="datasetacl",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)ss",
                to="auth.group",
            ),
        ),
        migrations.AlterField(
            model_name="datasetacl",
            name="token",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)ss",
                to="tardis_portal.token",
            ),
        ),
        migrations.AlterField(
            model_name="datasetacl",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)ss",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="datasetparameterset",
            name="storage_box",
            field=models.ManyToManyField(
                related_name="%(class)ss", to="tardis_portal.storagebox"
            ),
        ),
        migrations.AlterField(
            model_name="experiment",
            name="institution_name",
            field=models.CharField(default="Monash University", max_length=400),
        ),
        migrations.AlterField(
            model_name="experimentacl",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)ss",
                to="auth.group",
            ),
        ),
        migrations.AlterField(
            model_name="experimentacl",
            name="token",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)ss",
                to="tardis_portal.token",
            ),
        ),
        migrations.AlterField(
            model_name="experimentacl",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)ss",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="experimentparameterset",
            name="storage_box",
            field=models.ManyToManyField(
                related_name="%(class)ss", to="tardis_portal.storagebox"
            ),
        ),
        migrations.AlterField(
            model_name="instrumentparameterset",
            name="storage_box",
            field=models.ManyToManyField(
                related_name="%(class)ss", to="tardis_portal.storagebox"
            ),
        ),
        migrations.AlterField(
            model_name="storagebox",
            name="django_storage_class",
            field=models.TextField(
                default="tardis.tardis_portal.storage.MyTardisLocalFileSystemStorage"
            ),
        ),
        migrations.AlterField(
            model_name="userauthentication",
            name="authenticationMethod",
            field=models.CharField(choices=[("localdb", "Local DB")], max_length=30),
        ),
    ]
