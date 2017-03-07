# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import tardis.tardis_portal.models.parameters
import tardis.tardis_portal.models.token


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# tardis.tardis_portal.migrations.0005_datafile_add_size_int_column

def cast_string_to_integer(apps, schema_editor):
    DataFile = apps.get_model("tardis_portal", "DataFile")
    total_objects = DataFile.objects.all().count()

    print
    current_object = 0
    for df in DataFile.objects.all().iterator():
        df._size = long(df.size)
        df.save()
        current_object += 1
        if current_object % 10000 == 0:
            print "{0} of {1} datafile objects converted".format(
                    current_object, total_objects)


class Migration(migrations.Migration):
    # this migration has been squashed and transition to a normal migration
    # in case you need to run any of the individual/historic parts of it, please
    # check out a previous version, migrate, then continue with this one

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=400)),
                ('directory', models.CharField(null=True, blank=True, max_length=255)),
                ('size', models.CharField(max_length=400, blank=True)),
                ('created_time', models.DateTimeField(null=True, blank=True)),
                ('modification_time', models.DateTimeField(null=True, blank=True)),
                ('mimetype', models.CharField(max_length=80, blank=True)),
                ('md5sum', models.CharField(max_length=32, blank=True)),
                ('sha512sum', models.CharField(max_length=128, blank=True)),
                ('deleted', models.BooleanField(default=False)),
                ('deleted_time', models.DateTimeField(null=True, blank=True)),
                ('version', models.IntegerField(default=1)),
            ],
            options={
                'ordering': ['filename'],
            },
        ),
        migrations.CreateModel(
            name='DataFileObject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uri', models.TextField(null=True, blank=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('verified', models.BooleanField(default=False)),
                ('last_verified_time', models.DateTimeField(null=True, blank=True)),
                ('datafile', models.ForeignKey(related_name='file_objects', to='tardis_portal.DataFile')),
            ],
        ),
        migrations.CreateModel(
            name='DatafileParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string_value', models.TextField(null=True, blank=True)),
                ('numerical_value', models.FloatField(db_index=True, null=True, blank=True)),
                ('datetime_value', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('link_id', models.PositiveIntegerField(null=True, blank=True)),
                ('link_ct', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DatafileParameterSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datafile', models.ForeignKey(to='tardis_portal.DataFile')),
            ],
            options={
                'ordering': ['id'],
                'abstract': False,
            },
            bases=(models.Model, tardis.tardis_portal.models.parameters.ParameterSetManagerMixin),
        ),
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(blank=True)),
                ('directory', models.CharField(null=True, blank=True, max_length=255)),
                ('immutable', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='DatasetParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string_value', models.TextField(null=True, blank=True)),
                ('numerical_value', models.FloatField(db_index=True, null=True, blank=True)),
                ('datetime_value', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('link_id', models.PositiveIntegerField(null=True, blank=True)),
                ('link_ct', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DatasetParameterSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dataset', models.ForeignKey(to='tardis_portal.Dataset')),
            ],
            options={
                'ordering': ['id'],
                'abstract': False,
            },
            bases=(models.Model, tardis.tardis_portal.models.parameters.ParameterSetManagerMixin),
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(max_length=255, null=True, blank=True)),
                ('approved', models.BooleanField(default=False)),
                ('title', models.CharField(max_length=400)),
                ('institution_name', models.CharField(default=b'Monash University', max_length=400)),
                ('description', models.TextField(blank=True)),
                ('start_time', models.DateTimeField(null=True, blank=True)),
                ('end_time', models.DateTimeField(null=True, blank=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('handle', models.TextField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False)),
                ('public_access', models.PositiveSmallIntegerField(default=1, choices=[(1, b'No public access (hidden)'), (25, b'Ready to be released pending embargo expiry'), (50, b'Public Metadata only (no data file access)'), (100, b'Public')])),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ExperimentAuthor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('author', models.CharField(max_length=255)),
                ('institution', models.CharField(max_length=255, null=True, blank=True)),
                ('email', models.CharField(max_length=255, null=True, blank=True)),
                ('order', models.PositiveIntegerField()),
                ('url', models.URLField(help_text=b'URL identifier for the author', max_length=2000, null=True, blank=True)),
                ('experiment', models.ForeignKey(to='tardis_portal.Experiment')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='ExperimentParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string_value', models.TextField(null=True, blank=True)),
                ('numerical_value', models.FloatField(db_index=True, null=True, blank=True)),
                ('datetime_value', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('link_id', models.PositiveIntegerField(null=True, blank=True)),
                ('link_ct', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExperimentParameterSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('experiment', models.ForeignKey(to='tardis_portal.Experiment')),
            ],
            options={
                'ordering': ['id'],
                'abstract': False,
            },
            bases=(models.Model, tardis.tardis_portal.models.parameters.ParameterSetManagerMixin),
        ),
        migrations.CreateModel(
            name='Facility',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('manager_group', models.ForeignKey(to='auth.Group')),
            ],
            options={
                'verbose_name_plural': 'Facilities',
            },
        ),
        migrations.CreateModel(
            name='FreeTextSearchField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='GroupAdmin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.ForeignKey(to='auth.Group')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('facility', models.ForeignKey(to='tardis_portal.Facility')),
            ],
            options={
                'verbose_name_plural': 'Instruments',
            },
        ),
        migrations.CreateModel(
            name='InstrumentParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string_value', models.TextField(null=True, blank=True)),
                ('numerical_value', models.FloatField(db_index=True, null=True, blank=True)),
                ('datetime_value', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('link_id', models.PositiveIntegerField(null=True, blank=True)),
                ('link_ct', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InstrumentParameterSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('instrument', models.ForeignKey(to='tardis_portal.Instrument')),
            ],
            options={
                'ordering': ['id'],
                'abstract': False,
            },
            bases=(models.Model, tardis.tardis_portal.models.parameters.ParameterSetManagerMixin),
        ),
        migrations.CreateModel(
            name='JTI',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('jti', models.CharField(max_length=255)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=400)),
                ('url', models.URLField(help_text=b'Link to document outlining licensing details.', unique=True, max_length=255)),
                ('internal_description', models.TextField()),
                ('image_url', models.URLField(max_length=255, blank=True)),
                ('allows_distribution', models.BooleanField(default=False, help_text=b'Does this license provide distribution rights?')),
                ('is_active', models.BooleanField(default=True, help_text=b'Can experiments continue to select this license?')),
            ],
        ),
        migrations.CreateModel(
            name='ObjectACL',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pluginId', models.CharField(max_length=30)),
                ('entityId', models.CharField(max_length=320)),
                ('object_id', models.PositiveIntegerField()),
                ('canRead', models.BooleanField(default=False)),
                ('canWrite', models.BooleanField(default=False)),
                ('canDelete', models.BooleanField(default=False)),
                ('isOwner', models.BooleanField(default=False)),
                ('effectiveDate', models.DateField(null=True, blank=True)),
                ('expiryDate', models.DateField(null=True, blank=True)),
                ('aclOwnershipType', models.IntegerField(default=1, choices=[(1, b'Owner-owned'), (2, b'System-owned')])),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['content_type', 'object_id'],
                'verbose_name': 'Object ACL',
            },
        ),
        migrations.CreateModel(
            name='ParameterName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=60)),
                ('full_name', models.CharField(max_length=60)),
                ('units', models.CharField(max_length=60, blank=True)),
                ('data_type', models.IntegerField(default=2, choices=[(1, b'NUMERIC'), (2, b'STRING'), (3, b'URL'), (4, b'LINK'), (5, b'FILENAME'), (6, b'DATETIME'), (7, b'LONGSTRING')])),
                ('immutable', models.BooleanField(default=False)),
                ('comparison_type', models.IntegerField(default=1, choices=[(1, b'Exact value'), (8, b'Contains'), (3, b'Range'), (4, b'Greater than'), (5, b'Greater than or equal'), (6, b'Less than'), (7, b'Less than or equal')])),
                ('is_searchable', models.BooleanField(default=False)),
                ('choices', models.CharField(max_length=500, blank=True)),
                ('order', models.PositiveIntegerField(default=9999, null=True, blank=True)),
            ],
            options={
                'ordering': ('order', 'name'),
            },
        ),
        migrations.CreateModel(
            name='Schema',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('namespace', models.URLField(unique=True, max_length=255)),
                ('name', models.CharField(max_length=50, null=True, blank=True)),
                ('type', models.IntegerField(default=1, choices=[(1, b'Experiment schema'), (2, b'Dataset schema'), (3, b'Datafile schema'), (5, b'Instrument schema'), (4, b'None')])),
                ('subtype', models.CharField(max_length=30, null=True, blank=True)),
                ('immutable', models.BooleanField(default=False)),
                ('hidden', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='StorageBox',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('django_storage_class', models.TextField(default=b'tardis.tardis_portal.storage.MyTardisLocalFileSystemStorage')),
                ('max_size', models.BigIntegerField()),
                ('status', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=255, default=b'default', unique=True)),
                ('description', models.TextField(default=b'Default Storage')),
                ('master_box', models.ForeignKey(related_name='child_boxes', blank=True, to='tardis_portal.StorageBox', null=True)),
            ],
            options={
                'verbose_name_plural': 'storage boxes',
            },
        ),
        migrations.CreateModel(
            name='StorageBoxAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.TextField()),
                ('value', models.TextField()),
                ('storage_box', models.ForeignKey(related_name='attributes', to='tardis_portal.StorageBox')),
            ],
        ),
        migrations.CreateModel(
            name='StorageBoxOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.TextField()),
                ('value', models.TextField()),
                ('storage_box', models.ForeignKey(related_name='options', to='tardis_portal.StorageBox')),
                ('value_type', models.CharField(default=b'string', max_length=6, choices=[(b'string', b'String value'), (b'pickle', b'Pickled value')])),
            ],
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token', models.CharField(unique=True, max_length=30)),
                ('expiry_date', models.DateField(default=tardis.tardis_portal.models.token._token_expiry)),
                ('experiment', models.ForeignKey(to='tardis_portal.Experiment')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserAuthentication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(max_length=50)),
                ('authenticationMethod', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('isDjangoAccount', models.BooleanField(default=True)),
                ('rapidConnectEduPersonTargetedID', models.CharField(max_length=400, null=True, blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='userauthentication',
            name='userProfile',
            field=models.ForeignKey(to='tardis_portal.UserProfile'),
        ),
        migrations.AddField(
            model_name='parametername',
            name='schema',
            field=models.ForeignKey(to='tardis_portal.Schema'),
        ),
        migrations.AddField(
            model_name='instrumentparameterset',
            name='schema',
            field=models.ForeignKey(to='tardis_portal.Schema'),
        ),
        migrations.AddField(
            model_name='instrumentparameterset',
            name='storage_box',
            field=models.ManyToManyField(related_name='instrumentparametersets', to=b'tardis_portal.StorageBox'),
        ),
        migrations.AddField(
            model_name='instrumentparameter',
            name='name',
            field=models.ForeignKey(to='tardis_portal.ParameterName'),
        ),
        migrations.AddField(
            model_name='instrumentparameter',
            name='parameterset',
            field=models.ForeignKey(to='tardis_portal.InstrumentParameterSet'),
        ),
        migrations.AddField(
            model_name='freetextsearchfield',
            name='parameter_name',
            field=models.ForeignKey(to='tardis_portal.ParameterName'),
        ),
        migrations.AddField(
            model_name='experimentparameterset',
            name='schema',
            field=models.ForeignKey(to='tardis_portal.Schema'),
        ),
        migrations.AddField(
            model_name='experimentparameterset',
            name='storage_box',
            field=models.ManyToManyField(related_name='experimentparametersets', to=b'tardis_portal.StorageBox'),
        ),
        migrations.AddField(
            model_name='experimentparameter',
            name='name',
            field=models.ForeignKey(to='tardis_portal.ParameterName'),
        ),
        migrations.AddField(
            model_name='experimentparameter',
            name='parameterset',
            field=models.ForeignKey(to='tardis_portal.ExperimentParameterSet'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='license',
            field=models.ForeignKey(blank=True, to='tardis_portal.License', null=True),
        ),
        migrations.AddField(
            model_name='datasetparameterset',
            name='schema',
            field=models.ForeignKey(to='tardis_portal.Schema'),
        ),
        migrations.AddField(
            model_name='datasetparameterset',
            name='storage_box',
            field=models.ManyToManyField(related_name='datasetparametersets', to=b'tardis_portal.StorageBox'),
        ),
        migrations.AddField(
            model_name='datasetparameter',
            name='name',
            field=models.ForeignKey(to='tardis_portal.ParameterName'),
        ),
        migrations.AddField(
            model_name='datasetparameter',
            name='parameterset',
            field=models.ForeignKey(to='tardis_portal.DatasetParameterSet'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='experiments',
            field=models.ManyToManyField(related_name='datasets', to=b'tardis_portal.Experiment'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='instrument',
            field=models.ForeignKey(blank=True, to='tardis_portal.Instrument', null=True),
        ),
        migrations.AddField(
            model_name='datafileparameterset',
            name='schema',
            field=models.ForeignKey(to='tardis_portal.Schema'),
        ),
        migrations.AddField(
            model_name='datafileparameterset',
            name='storage_box',
            field=models.ManyToManyField(related_name='datafileparametersets', to=b'tardis_portal.StorageBox'),
        ),
        migrations.AddField(
            model_name='datafileparameter',
            name='name',
            field=models.ForeignKey(to='tardis_portal.ParameterName'),
        ),
        migrations.AddField(
            model_name='datafileparameter',
            name='parameterset',
            field=models.ForeignKey(to='tardis_portal.DatafileParameterSet'),
        ),
        migrations.AddField(
            model_name='datafileobject',
            name='storage_box',
            field=models.ForeignKey(related_name='file_objects', to='tardis_portal.StorageBox'),
        ),
        migrations.AddField(
            model_name='datafile',
            name='dataset',
            field=models.ForeignKey(to='tardis_portal.Dataset'),
        ),
        migrations.AlterUniqueTogether(
            name='parametername',
            unique_together=set([('schema', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='experimentauthor',
            unique_together=set([('experiment', 'author')]),
        ),
        migrations.AlterUniqueTogether(
            name='datafileobject',
            unique_together=set([('datafile', 'storage_box')]),
        ),
        migrations.AlterUniqueTogether(
            name='datafile',
            unique_together=set([('dataset', 'directory', 'filename', 'version')]),
        ),
        migrations.AlterField(
            model_name='parametername',
            name='data_type',
            field=models.IntegerField(default=2, choices=[(1, b'NUMERIC'), (2, b'STRING'), (3, b'URL'), (4, b'LINK'), (5, b'FILENAME'), (6, b'DATETIME'), (7, b'LONGSTRING'), (8, b'JSON')]),
        ),
        migrations.AddField(
            model_name='datafile',
            name='_size',
            field=models.BigIntegerField(null=True, blank=True),
        ),
        #migrations.RunPython(
        #    code=tardis.tardis_portal.migrations.0005_datafile_add_size_int_column.cast_string_to_integer,
        #),
        migrations.RunPython(
            cast_string_to_integer
        ),
        migrations.RemoveField(
            model_name='datafile',
            name='size',
        ),
        migrations.RenameField(
            model_name='datafile',
            old_name='_size',
            new_name='size',
        ),
        migrations.AlterUniqueTogether(
            name='instrument',
            unique_together=set([('name', 'facility')]),
        ),
        migrations.AlterField(
            model_name='datafile',
            name='mimetype',
            field=models.CharField(db_index=True, max_length=80, blank=True),
        ),
        migrations.AlterField(
            model_name='datafile',
            name='directory',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='directory',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='experimentauthor',
            name='url',
            field=models.URLField(help_text=b'URL identifier for the author', max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='license',
            name='image_url',
            field=models.URLField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='license',
            name='name',
            field=models.CharField(unique=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='license',
            name='url',
            field=models.URLField(help_text=b'Link to document outlining licensing details.', max_length=255),
        ),
        migrations.AlterField(
            model_name='storagebox',
            name='name',
            field=models.CharField(default=b'default', unique=True, max_length=255),
        ),
    ]
