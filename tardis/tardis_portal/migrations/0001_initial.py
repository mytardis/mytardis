# encoding: utf-8


import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'UserProfile'
        db.create_table('tardis_portal_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('isDjangoAccount', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('tardis_portal', ['UserProfile'])

        # Adding model 'GroupAdmin'
        db.create_table('tardis_portal_groupadmin', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'])),
        ))
        db.send_create_signal('tardis_portal', ['GroupAdmin'])

        # Adding model 'UserAuthentication'
        db.create_table('tardis_portal_userauthentication', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('userProfile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.UserProfile'])),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('authenticationMethod', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal('tardis_portal', ['UserAuthentication'])

        # Adding model 'XSLT_docs'
        db.create_table('tardis_portal_xslt_docs', (
            ('xmlns', self.gf('django.db.models.fields.URLField')(max_length=255, primary_key=True)),
            ('data', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('tardis_portal', ['XSLT_docs'])

        # Adding model 'Experiment'
        db.create_table('tardis_portal_experiment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=255, null=True, blank=True)),
            ('approved', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('institution_name', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('end_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('update_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('handle', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('tardis_portal', ['Experiment'])

        # Adding model 'ExperimentACL'
        db.create_table('tardis_portal_experimentacl', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pluginId', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('entityId', self.gf('django.db.models.fields.CharField')(max_length=320)),
            ('experiment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.Experiment'])),
            ('canRead', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('canWrite', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('canDelete', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('isOwner', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('effectiveDate', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('expiryDate', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('aclOwnershipType', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal('tardis_portal', ['ExperimentACL'])

        # Adding model 'Author_Experiment'
        db.create_table('tardis_portal_author_experiment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('experiment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.Experiment'])),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('tardis_portal', ['Author_Experiment'])

        # Adding unique constraint on 'Author_Experiment', fields ['experiment', 'author']
        db.create_unique('tardis_portal_author_experiment', ['experiment_id', 'author'])

        # Adding model 'Dataset'
        db.create_table('tardis_portal_dataset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('experiment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.Experiment'])),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('tardis_portal', ['Dataset'])

        # Adding model 'Dataset_File'
        db.create_table('tardis_portal_dataset_file', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dataset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.Dataset'])),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('size', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True)),
            ('protocol', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('modification_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('mimetype', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
            ('md5sum', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
        ))
        db.send_create_signal('tardis_portal', ['Dataset_File'])

        # Adding model 'Schema'
        db.create_table('tardis_portal_schema', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('namespace', self.gf('django.db.models.fields.URLField')(max_length=400)),
        ))
        db.send_create_signal('tardis_portal', ['Schema'])

        # Adding model 'DatafileParameterSet'
        db.create_table('tardis_portal_datafileparameterset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.Schema'])),
            ('dataset_file', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.Dataset_File'])),
        ))
        db.send_create_signal('tardis_portal', ['DatafileParameterSet'])

        # Adding model 'DatasetParameterSet'
        db.create_table('tardis_portal_datasetparameterset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.Schema'])),
            ('dataset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.Dataset'])),
        ))
        db.send_create_signal('tardis_portal', ['DatasetParameterSet'])

        # Adding model 'ExperimentParameterSet'
        db.create_table('tardis_portal_experimentparameterset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.Schema'])),
            ('experiment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.Experiment'])),
        ))
        db.send_create_signal('tardis_portal', ['ExperimentParameterSet'])

        # Adding model 'ParameterName'
        db.create_table('tardis_portal_parametername', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.Schema'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('full_name', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('units', self.gf('django.db.models.fields.CharField')(max_length=60, blank=True)),
            ('is_numeric', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('comparison_type', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('is_searchable', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('choices', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
        ))
        db.send_create_signal('tardis_portal', ['ParameterName'])

        # Adding model 'DatafileParameter'
        db.create_table('tardis_portal_datafileparameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parameterset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.DatafileParameterSet'])),
            ('name', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.ParameterName'])),
            ('string_value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('numerical_value', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal('tardis_portal', ['DatafileParameter'])

        # Adding model 'DatasetParameter'
        db.create_table('tardis_portal_datasetparameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parameterset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.DatasetParameterSet'])),
            ('name', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.ParameterName'])),
            ('string_value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('numerical_value', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal('tardis_portal', ['DatasetParameter'])

        # Adding model 'ExperimentParameter'
        db.create_table('tardis_portal_experimentparameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parameterset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.ExperimentParameterSet'])),
            ('name', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tardis_portal.ParameterName'])),
            ('string_value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('numerical_value', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal('tardis_portal', ['ExperimentParameter'])

        # Adding model 'XML_data'
        db.create_table('tardis_portal_xml_data', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('datafile', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tardis_portal.Dataset_File'], unique=True, null=True, blank=True)),
            ('dataset', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tardis_portal.Dataset'], unique=True, null=True, blank=True)),
            ('experiment', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tardis_portal.Experiment'], unique=True, null=True, blank=True)),
            ('xmlns', self.gf('django.db.models.fields.URLField')(max_length=400)),
            ('data', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('tardis_portal', ['XML_data'])

        # Adding model 'Equipment'
        db.create_table('tardis_portal_equipment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('make', self.gf('django.db.models.fields.CharField')(max_length=60, blank=True)),
            ('model', self.gf('django.db.models.fields.CharField')(max_length=60, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=60, blank=True)),
            ('serial', self.gf('django.db.models.fields.CharField')(max_length=60, blank=True)),
            ('comm', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('decomm', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('tardis_portal', ['Equipment'])

        # Adding M2M table for field dataset on 'Equipment'
        db.create_table('tardis_portal_equipment_dataset', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('equipment', models.ForeignKey(orm['tardis_portal.equipment'], null=False)),
            ('dataset', models.ForeignKey(orm['tardis_portal.dataset'], null=False))
        ))
        db.create_unique('tardis_portal_equipment_dataset', ['equipment_id', 'dataset_id'])

    def backwards(self, orm):

        # Removing unique constraint on 'Author_Experiment', fields ['experiment', 'author']
        db.delete_unique('tardis_portal_author_experiment', ['experiment_id', 'author'])

        # Deleting model 'UserProfile'
        db.delete_table('tardis_portal_userprofile')

        # Deleting model 'GroupAdmin'
        db.delete_table('tardis_portal_groupadmin')

        # Deleting model 'UserAuthentication'
        db.delete_table('tardis_portal_userauthentication')

        # Deleting model 'XSLT_docs'
        db.delete_table('tardis_portal_xslt_docs')

        # Deleting model 'Experiment'
        db.delete_table('tardis_portal_experiment')

        # Deleting model 'ExperimentACL'
        db.delete_table('tardis_portal_experimentacl')

        # Deleting model 'Author_Experiment'
        db.delete_table('tardis_portal_author_experiment')

        # Deleting model 'Dataset'
        db.delete_table('tardis_portal_dataset')

        # Deleting model 'Dataset_File'
        db.delete_table('tardis_portal_dataset_file')

        # Deleting model 'Schema'
        db.delete_table('tardis_portal_schema')

        # Deleting model 'DatafileParameterSet'
        db.delete_table('tardis_portal_datafileparameterset')

        # Deleting model 'DatasetParameterSet'
        db.delete_table('tardis_portal_datasetparameterset')

        # Deleting model 'ExperimentParameterSet'
        db.delete_table('tardis_portal_experimentparameterset')

        # Deleting model 'ParameterName'
        db.delete_table('tardis_portal_parametername')

        # Deleting model 'DatafileParameter'
        db.delete_table('tardis_portal_datafileparameter')

        # Deleting model 'DatasetParameter'
        db.delete_table('tardis_portal_datasetparameter')

        # Deleting model 'ExperimentParameter'
        db.delete_table('tardis_portal_experimentparameter')

        # Deleting model 'XML_data'
        db.delete_table('tardis_portal_xml_data')

        # Deleting model 'Equipment'
        db.delete_table('tardis_portal_equipment')

        # Removing M2M table for field dataset on 'Equipment'
        db.delete_table('tardis_portal_equipment_dataset')

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
            'order': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'tardis_portal.datafileparameter': {
            'Meta': {'ordering': "['id']", 'object_name': 'DatafileParameter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ParameterName']"}),
            'numerical_value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'parameterset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.DatafileParameterSet']"}),
            'string_value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
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
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Experiment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
            'size': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '400'})
        },
        'tardis_portal.datasetparameter': {
            'Meta': {'ordering': "['id']", 'object_name': 'DatasetParameter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ParameterName']"}),
            'numerical_value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'parameterset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.DatasetParameterSet']"}),
            'string_value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'tardis_portal.datasetparameterset': {
            'Meta': {'ordering': "['id']", 'object_name': 'DatasetParameterSet'},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Dataset']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Schema']"})
        },
        'tardis_portal.equipment': {
            'Meta': {'object_name': 'Equipment'},
            'comm': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'dataset': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['tardis_portal.Dataset']", 'null': 'True', 'blank': 'True'}),
            'decomm': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'make': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'serial': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
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
            'institution_name': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'Meta': {'ordering': "['id']", 'object_name': 'ExperimentParameter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ParameterName']"}),
            'numerical_value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'parameterset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.ExperimentParameterSet']"}),
            'string_value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'tardis_portal.experimentparameterset': {
            'Meta': {'ordering': "['id']", 'object_name': 'ExperimentParameterSet'},
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Experiment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Schema']"})
        },
        'tardis_portal.groupadmin': {
            'Meta': {'object_name': 'GroupAdmin'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'tardis_portal.parametername': {
            'Meta': {'object_name': 'ParameterName'},
            'choices': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'comparison_type': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_numeric': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_searchable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tardis_portal.Schema']"}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'})
        },
        'tardis_portal.schema': {
            'Meta': {'object_name': 'Schema'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'namespace': ('django.db.models.fields.URLField', [], {'max_length': '400'})
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
        },
        'tardis_portal.xml_data': {
            'Meta': {'object_name': 'XML_data'},
            'data': ('django.db.models.fields.TextField', [], {}),
            'datafile': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tardis_portal.Dataset_File']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'dataset': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tardis_portal.Dataset']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'experiment': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tardis_portal.Experiment']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'xmlns': ('django.db.models.fields.URLField', [], {'max_length': '400'})
        },
        'tardis_portal.xslt_docs': {
            'Meta': {'object_name': 'XSLT_docs'},
            'data': ('django.db.models.fields.TextField', [], {}),
            'xmlns': ('django.db.models.fields.URLField', [], {'max_length': '255', 'primary_key': 'True'})
        }
    }

    complete_apps = ['tardis_portal']
