# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'DataFile', fields ['directory', 'version', 'filename']
        db.delete_unique(u'tardis_portal_datafile', ['directory', 'version', 'filename'])

        # Adding unique constraint on 'DataFile', fields ['directory', 'filename', 'version', 'dataset']
        db.create_unique(u'tardis_portal_datafile', ['directory', 'filename', 'version', 'dataset_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'DataFile', fields ['directory', 'filename', 'version', 'dataset']
        db.delete_unique(u'tardis_portal_datafile', ['directory', 'filename', 'version', 'dataset_id'])

        # Adding unique constraint on 'DataFile', fields ['directory', 'version', 'filename']
        db.create_unique(u'tardis_portal_datafile', ['directory', 'version', 'filename'])


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'tardis_portal.author_experiment': {
            'Meta': {'ordering': "['order']", 'unique_together': "(('experiment', 'author'),)", 'object_name': 'Author_Experiment'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Experiment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '2000', 'blank': 'True'})
        },
        'tardis_portal.datafile': {
            'Meta': {'ordering': "['filename']", 'unique_together': "(['dataset', 'directory', 'filename', 'version'],)", 'object_name': 'DataFile'},
            'created_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Dataset']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'deleted_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'directory': ('tardis.tardis_portal.models.fields.DirectoryField', [], {'null': 'True', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md5sum': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'mimetype': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'modification_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sha512sum': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'size': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'version': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'tardis_portal.datafileobject': {
            'Meta': {'unique_together': "(['datafile', 'storage_box'],)", 'object_name': 'DataFileObject'},
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datafile': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'file_objects'", 'to': "orm['tardis_portal.DataFile']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_verified_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'storage_box': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'file_objects'", 'to': "orm['tardis_portal.StorageBox']"}),
            'uri': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'tardis_portal.datafileparameter': {
            'Meta': {'ordering': "['name']", 'object_name': 'DatafileParameter'},
            'datetime_value': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ParameterName']"}),
            'numerical_value': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'parameterset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.DatafileParameterSet']"}),
            'string_value': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        'tardis_portal.datafileparameterset': {
            'Meta': {'ordering': "['id']", 'object_name': 'DatafileParameterSet'},
            'datafile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.DataFile']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Schema']"}),
            'storage_box': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'datafileparametersets'", 'symmetrical': 'False', 'to': "orm['tardis_portal.StorageBox']"})
        },
        'tardis_portal.dataset': {
            'Meta': {'ordering': "['-id']", 'object_name': 'Dataset'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'directory': ('tardis.tardis_portal.models.fields.DirectoryField', [], {'null': 'True', 'blank': 'True'}),
            'experiments': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'datasets'", 'symmetrical': 'False', 'to': "orm['tardis_portal.Experiment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'immutable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'storage_boxes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'datasets'", 'blank': 'True', 'to': "orm['tardis_portal.StorageBox']"})
        },
        'tardis_portal.datasetparameter': {
            'Meta': {'ordering': "['name']", 'object_name': 'DatasetParameter'},
            'datetime_value': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ParameterName']"}),
            'numerical_value': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'parameterset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.DatasetParameterSet']"}),
            'string_value': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        'tardis_portal.datasetparameterset': {
            'Meta': {'ordering': "['id']", 'object_name': 'DatasetParameterSet'},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Dataset']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Schema']"}),
            'storage_box': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'datasetparametersets'", 'symmetrical': 'False', 'to': "orm['tardis_portal.StorageBox']"})
        },
        'tardis_portal.experiment': {
            'Meta': {'object_name': 'Experiment'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'handle': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution_name': ('django.db.models.fields.CharField', [], {'default': "'Monash University'", 'max_length': '400'}),
            'license': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.License']", 'null': 'True', 'blank': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public_access': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'tardis_portal.experimentparameter': {
            'Meta': {'ordering': "['name']", 'object_name': 'ExperimentParameter'},
            'datetime_value': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ParameterName']"}),
            'numerical_value': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'parameterset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ExperimentParameterSet']"}),
            'string_value': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        'tardis_portal.experimentparameterset': {
            'Meta': {'ordering': "['id']", 'object_name': 'ExperimentParameterSet'},
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Experiment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Schema']"}),
            'storage_box': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'experimentparametersets'", 'symmetrical': 'False', 'to': "orm['tardis_portal.StorageBox']"})
        },
        'tardis_portal.freetextsearchfield': {
            'Meta': {'object_name': 'FreeTextSearchField'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter_name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ParameterName']"})
        },
        'tardis_portal.groupadmin': {
            'Meta': {'object_name': 'GroupAdmin'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'tardis_portal.license': {
            'Meta': {'object_name': 'License'},
            'allows_distribution': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_url': ('django.db.models.fields.URLField', [], {'max_length': '2000', 'blank': 'True'}),
            'internal_description': ('django.db.models.fields.TextField', [], {}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '400'}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '2000'})
        },
        'tardis_portal.objectacl': {
            'Meta': {'ordering': "['content_type', 'object_id']", 'object_name': 'ObjectACL'},
            'aclOwnershipType': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'canDelete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'canRead': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'canWrite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'effectiveDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'entityId': ('django.db.models.fields.CharField', [], {'max_length': '320'}),
            'expiryDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isOwner': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'pluginId': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'tardis_portal.parametername': {
            'Meta': {'ordering': "('order', 'name')", 'unique_together': "(('schema', 'name'),)", 'object_name': 'ParameterName'},
            'choices': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'comparison_type': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'data_type': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'immutable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_searchable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '9999', 'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Schema']"}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'})
        },
        'tardis_portal.schema': {
            'Meta': {'object_name': 'Schema'},
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'immutable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'namespace': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '255'}),
            'subtype': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'tardis_portal.storagebox': {
            'Meta': {'object_name': 'StorageBox'},
            'description': ('django.db.models.fields.TextField', [], {'default': "'Default Storage'"}),
            'django_storage_class': ('django.db.models.fields.TextField', [], {'default': "'tardis.tardis_portal.storage.MyTardisLocalFileSystemStorage'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_size': ('django.db.models.fields.BigIntegerField', [], {}),
            'name': ('django.db.models.fields.TextField', [], {'default': "'default'", 'unique': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'tardis_portal.storageboxattribute': {
            'Meta': {'object_name': 'StorageBoxAttribute'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.TextField', [], {}),
            'storage_box': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attributes'", 'to': "orm['tardis_portal.StorageBox']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'tardis_portal.storageboxoption': {
            'Meta': {'object_name': 'StorageBoxOption'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.TextField', [], {}),
            'storage_box': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': "orm['tardis_portal.StorageBox']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'tardis_portal.token': {
            'Meta': {'object_name': 'Token'},
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Experiment']"}),
            'expiry_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 10, 1, 0, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'tardis_portal.userauthentication': {
            'Meta': {'object_name': 'UserAuthentication'},
            'authenticationMethod': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'userProfile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.UserProfile']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'tardis_portal.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isDjangoAccount': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['tardis_portal']