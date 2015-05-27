# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tardis.tardis_portal.models.parameters
import tardis.tardis_portal.models.fields
from django.conf import settings
import tardis.tardis_portal.models.token


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=400)),
                ('directory', tardis.tardis_portal.models.fields.DirectoryField(null=True, blank=True)),
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
            bases=(models.Model,),
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
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DatafileParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string_value', models.TextField(db_index=True, null=True, blank=True)),
                ('numerical_value', models.FloatField(db_index=True, null=True, blank=True)),
                ('datetime_value', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('link_id', models.PositiveIntegerField(null=True, blank=True)),
                ('link_ct', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
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
                ('directory', tardis.tardis_portal.models.fields.DirectoryField(null=True, blank=True)),
                ('immutable', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-id'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DatasetParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string_value', models.TextField(db_index=True, null=True, blank=True)),
                ('numerical_value', models.FloatField(db_index=True, null=True, blank=True)),
                ('datetime_value', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('link_id', models.PositiveIntegerField(null=True, blank=True)),
                ('link_ct', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
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
            options={
            },
            bases=(models.Model,),
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
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExperimentParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string_value', models.TextField(db_index=True, null=True, blank=True)),
                ('numerical_value', models.FloatField(db_index=True, null=True, blank=True)),
                ('datetime_value', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('link_id', models.PositiveIntegerField(null=True, blank=True)),
                ('link_ct', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
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
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FreeTextSearchField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroupAdmin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.ForeignKey(to='auth.Group')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
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
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InstrumentParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string_value', models.TextField(db_index=True, null=True, blank=True)),
                ('numerical_value', models.FloatField(db_index=True, null=True, blank=True)),
                ('datetime_value', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('link_id', models.PositiveIntegerField(null=True, blank=True)),
                ('link_ct', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
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
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=400)),
                ('url', models.URLField(help_text=b'Link to document outlining licensing details.', unique=True, max_length=2000)),
                ('internal_description', models.TextField()),
                ('image_url', models.URLField(max_length=2000, blank=True)),
                ('allows_distribution', models.BooleanField(default=False, help_text=b'Does this license provide distribution rights?')),
                ('is_active', models.BooleanField(default=True, help_text=b'Can experiments continue to select this license?')),
            ],
            options={
            },
            bases=(models.Model,),
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
            bases=(models.Model,),
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
            bases=(models.Model,),
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
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StorageBox',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('django_storage_class', models.TextField(default=b'tardis.tardis_portal.storage.MyTardisLocalFileSystemStorage')),
                ('max_size', models.BigIntegerField()),
                ('status', models.CharField(max_length=100)),
                ('name', models.TextField(default=b'default', unique=True)),
                ('description', models.TextField(default=b'Default Storage')),
                ('master_box', models.ForeignKey(related_name='child_boxes', blank=True, to='tardis_portal.StorageBox', null=True)),
            ],
            options={
                'verbose_name_plural': 'storage boxes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StorageBoxAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.TextField()),
                ('value', models.TextField()),
                ('storage_box', models.ForeignKey(related_name='attributes', to='tardis_portal.StorageBox')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StorageBoxOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.TextField()),
                ('value', models.TextField()),
                ('storage_box', models.ForeignKey(related_name='options', to='tardis_portal.StorageBox')),
            ],
            options={
            },
            bases=(models.Model,),
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
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserAuthentication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(max_length=50)),
                ('authenticationMethod', models.CharField(max_length=30)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('isDjangoAccount', models.BooleanField(default=True)),
                ('rapidConnectEduPersonTargetedID', models.CharField(max_length=400, null=True, blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='userauthentication',
            name='userProfile',
            field=models.ForeignKey(to='tardis_portal.UserProfile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='parametername',
            name='schema',
            field=models.ForeignKey(to='tardis_portal.Schema'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='parametername',
            unique_together=set([('schema', 'name')]),
        ),
        migrations.AddField(
            model_name='instrumentparameterset',
            name='schema',
            field=models.ForeignKey(to='tardis_portal.Schema'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='instrumentparameterset',
            name='storage_box',
            field=models.ManyToManyField(related_name='instrumentparametersets', to='tardis_portal.StorageBox'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='instrumentparameter',
            name='name',
            field=models.ForeignKey(to='tardis_portal.ParameterName'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='instrumentparameter',
            name='parameterset',
            field=models.ForeignKey(to='tardis_portal.InstrumentParameterSet'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='freetextsearchfield',
            name='parameter_name',
            field=models.ForeignKey(to='tardis_portal.ParameterName'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='experimentparameterset',
            name='schema',
            field=models.ForeignKey(to='tardis_portal.Schema'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='experimentparameterset',
            name='storage_box',
            field=models.ManyToManyField(related_name='experimentparametersets', to='tardis_portal.StorageBox'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='experimentparameter',
            name='name',
            field=models.ForeignKey(to='tardis_portal.ParameterName'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='experimentparameter',
            name='parameterset',
            field=models.ForeignKey(to='tardis_portal.ExperimentParameterSet'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='experimentauthor',
            unique_together=set([('experiment', 'author')]),
        ),
        migrations.AddField(
            model_name='experiment',
            name='license',
            field=models.ForeignKey(blank=True, to='tardis_portal.License', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datasetparameterset',
            name='schema',
            field=models.ForeignKey(to='tardis_portal.Schema'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datasetparameterset',
            name='storage_box',
            field=models.ManyToManyField(related_name='datasetparametersets', to='tardis_portal.StorageBox'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datasetparameter',
            name='name',
            field=models.ForeignKey(to='tardis_portal.ParameterName'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datasetparameter',
            name='parameterset',
            field=models.ForeignKey(to='tardis_portal.DatasetParameterSet'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dataset',
            name='experiments',
            field=models.ManyToManyField(related_name='datasets', to='tardis_portal.Experiment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dataset',
            name='instrument',
            field=models.ForeignKey(blank=True, to='tardis_portal.Instrument', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datafileparameterset',
            name='schema',
            field=models.ForeignKey(to='tardis_portal.Schema'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datafileparameterset',
            name='storage_box',
            field=models.ManyToManyField(related_name='datafileparametersets', to='tardis_portal.StorageBox'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datafileparameter',
            name='name',
            field=models.ForeignKey(to='tardis_portal.ParameterName'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datafileparameter',
            name='parameterset',
            field=models.ForeignKey(to='tardis_portal.DatafileParameterSet'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='datafileobject',
            name='storage_box',
            field=models.ForeignKey(related_name='file_objects', to='tardis_portal.StorageBox'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='datafileobject',
            unique_together=set([('datafile', 'storage_box')]),
        ),
        migrations.AddField(
            model_name='datafile',
            name='dataset',
            field=models.ForeignKey(to='tardis_portal.Dataset'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='datafile',
            unique_together=set([('dataset', 'directory', 'filename', 'version')]),
        ),
    ]
