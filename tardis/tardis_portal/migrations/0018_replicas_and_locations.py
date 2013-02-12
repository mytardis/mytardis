# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Replica'
        db.create_table('tardis_portal_replica', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('datafile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.Dataset_File'])),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('protocol', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('verified', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('stay_remote', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.Location'])),
        ))
        db.send_create_signal('tardis_portal', ['Replica'])

        # Adding unique constraint on 'Replica', fields ['datafile', 'location']
        db.create_unique('tardis_portal_replica', ['datafile_id', 'location_id'])

        # Adding model 'Location'
        db.create_table('tardis_portal_location', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=10, unique=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=400, unique=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('priority', self.gf('django.db.models.fields.IntegerField')()),
            ('is_available', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('trust_length', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('metadata_supported', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('auth_user', self.gf('django.db.models.fields.CharField')(default='', max_length=20)),
            ('auth_password', self.gf('django.db.models.fields.CharField')(default='', max_length=400)),
            ('auth_realm', self.gf('django.db.models.fields.CharField')(default='', max_length=20)),
            ('auth_scheme', self.gf('django.db.models.fields.CharField')(default='digest', max_length=10)),
            ('migration_provider', self.gf('django.db.models.fields.CharField')(default='local', max_length=10)),
        ))
        db.send_create_signal('tardis_portal', ['Location'])


    def backwards(self, orm):
        # Removing unique constraint on 'Replica', fields ['datafile', 'location']
        db.delete_unique('tardis_portal_replica', ['datafile_id', 'location_id'])

        # Deleting model 'Replica'
        db.delete_table('tardis_portal_replica')

        # Deleting model 'Location'
        db.delete_table('tardis_portal_location')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'tardis_portal.author_experiment': {
            'Meta': {'ordering': "['order']", 'unique_together': "(('experiment', 'author'),)", 'object_name': 'Author_Experiment'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Experiment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '2000', 'blank': 'True'})
        },
        'tardis_portal.datafileparameter': {
            'Meta': {'ordering': "['name']", 'object_name': 'DatafileParameter'},
            'datetime_value': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ParameterName']"}),
            'numerical_value': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'parameterset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.DatafileParameterSet']"}),
            'string_value': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        'tardis_portal.datafileparameterset': {
            'Meta': {'ordering': "['id']", 'object_name': 'DatafileParameterSet'},
            'dataset_file': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Dataset_File']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Schema']"})
        },
        'tardis_portal.dataset': {
            'Meta': {'object_name': 'Dataset'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'experiments': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'datasets'", 'symmetrical': 'False', 'to': "orm['tardis_portal.Experiment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'immutable': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'tardis_portal.dataset_file': {
            'Meta': {'object_name': 'Dataset_File'},
            'created_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Dataset']"}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md5sum': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'mimetype': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'modification_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'protocol': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'sha512sum': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'size': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'stay_remote': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'tardis_portal.datasetparameter': {
            'Meta': {'ordering': "['name']", 'object_name': 'DatasetParameter'},
            'datetime_value': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ParameterName']"}),
            'numerical_value': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'parameterset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.DatasetParameterSet']"}),
            'string_value': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        'tardis_portal.datasetparameterset': {
            'Meta': {'ordering': "['id']", 'object_name': 'DatasetParameterSet'},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Dataset']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Schema']"})
        },
        'tardis_portal.experiment': {
            'Meta': {'object_name': 'Experiment'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'handle': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution_name': ('django.db.models.fields.CharField', [], {'default': "'The University of Queensland'", 'max_length': '400'}),
            'license': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.License']", 'null': 'True', 'blank': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public_access': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'tardis_portal.experimentacl': {
            'Meta': {'ordering': "['experiment__id']", 'object_name': 'ExperimentACL'},
            'aclOwnershipType': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'canDelete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'canRead': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'canWrite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'effectiveDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'entityId': ('django.db.models.fields.CharField', [], {'max_length': '320'}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Experiment']"}),
            'expiryDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isOwner': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pluginId': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'tardis_portal.experimentparameter': {
            'Meta': {'ordering': "['name']", 'object_name': 'ExperimentParameter'},
            'datetime_value': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ParameterName']"}),
            'numerical_value': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'parameterset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ExperimentParameterSet']"}),
            'string_value': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        'tardis_portal.experimentparameterset': {
            'Meta': {'ordering': "['id']", 'object_name': 'ExperimentParameterSet'},
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Experiment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Schema']"})
        },
        'tardis_portal.freetextsearchfield': {
            'Meta': {'object_name': 'FreeTextSearchField'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter_name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ParameterName']"})
        },
        'tardis_portal.groupadmin': {
            'Meta': {'object_name': 'GroupAdmin'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'tardis_portal.license': {
            'Meta': {'object_name': 'License'},
            'allows_distribution': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_url': ('django.db.models.fields.URLField', [], {'max_length': '2000', 'blank': 'True'}),
            'internal_description': ('django.db.models.fields.TextField', [], {}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '400'}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '2000'})
        },
        'tardis_portal.location': {
            'Meta': {'object_name': 'Location'},
            'auth_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '400'}),
            'auth_realm': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20'}),
            'auth_scheme': ('django.db.models.fields.CharField', [], {'default': "'digest'", 'max_length': '10'}),
            'auth_user': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_available': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'metadata_supported': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'migration_provider': ('django.db.models.fields.CharField', [], {'default': "'local'", 'max_length': '10'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'priority': ('django.db.models.fields.IntegerField', [], {}),
            'trust_length': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '400'})
        },
        'tardis_portal.parametername': {
            'Meta': {'ordering': "('order', 'name')", 'unique_together': "(('schema', 'name'),)", 'object_name': 'ParameterName'},
            'choices': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'comparison_type': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'data_type': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'immutable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_searchable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '9999', 'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Schema']"}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'})
        },
        'tardis_portal.replica': {
            'Meta': {'unique_together': "(('datafile', 'location'),)", 'object_name': 'Replica'},
            'datafile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Dataset_File']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Location']"}),
            'protocol': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'stay_remote': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'tardis_portal.schema': {
            'Meta': {'object_name': 'Schema'},
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'immutable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'namespace': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '255'}),
            'subtype': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'tardis_portal.token': {
            'Meta': {'object_name': 'Token'},
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Experiment']"}),
            'expiry_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 3, 8, 0, 0)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'tardis_portal.userauthentication': {
            'Meta': {'object_name': 'UserAuthentication'},
            'authenticationMethod': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'userProfile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.UserProfile']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'tardis_portal.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isDjangoAccount': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['tardis_portal']
