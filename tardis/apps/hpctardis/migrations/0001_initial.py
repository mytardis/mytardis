# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'PartyRecord'
        db.create_table('hpctardis_partyrecord', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('name_title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('name_given', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('name_family', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('location', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal('hpctardis', ['PartyRecord'])

        # Adding model 'ActivityRecord'
        db.create_table('hpctardis_activityrecord', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('type', self.gf('django.db.models.fields.CharField')(default='', max_length=80)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal('hpctardis', ['ActivityRecord'])


    def backwards(self, orm):
        
        # Deleting model 'PartyRecord'
        db.delete_table('hpctardis_partyrecord')

        # Deleting model 'ActivityRecord'
        db.delete_table('hpctardis_activityrecord')


    models = {
        'hpctardis.activityrecord': {
            'Meta': {'object_name': 'ActivityRecord'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'})
        },
        'hpctardis.partyrecord': {
            'Meta': {'object_name': 'PartyRecord'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'location': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name_title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        }
    }

    complete_apps = ['hpctardis']
