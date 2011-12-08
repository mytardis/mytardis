# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ActivityLocation'
        db.create_table('hpctardis_activitylocation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='url', max_length=80)),
            ('value', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('activity', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hpctardis.ActivityRecord'])),
        ))
        db.send_create_signal('hpctardis', ['ActivityLocation'])

        # Adding model 'PartyLocation'
        db.create_table('hpctardis_partylocation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='url', max_length=80)),
            ('value', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hpctardis.PartyRecord'])),
        ))
        db.send_create_signal('hpctardis', ['PartyLocation'])


    def backwards(self, orm):
        
        # Deleting model 'ActivityLocation'
        db.delete_table('hpctardis_activitylocation')

        # Deleting model 'PartyLocation'
        db.delete_table('hpctardis_partylocation')


    models = {
        'hpctardis.activitylocation': {
            'Meta': {'object_name': 'ActivityLocation'},
            'activity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hpctardis.ActivityRecord']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'url'", 'max_length': '80'}),
            'value': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        'hpctardis.activitypartyrelation': {
            'Meta': {'object_name': 'ActivityPartyRelation'},
            'activity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hpctardis.ActivityRecord']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hpctardis.PartyRecord']"}),
            'relation': ('django.db.models.fields.CharField', [], {'default': "'isManagedBy'", 'max_length': '80'})
        },
        'hpctardis.activityrecord': {
            'Meta': {'object_name': 'ActivityRecord'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['hpctardis.LocationRecord']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'parties': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['hpctardis.PartyRecord']", 'through': "orm['hpctardis.ActivityPartyRelation']", 'symmetrical': 'False'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'})
        },
        'hpctardis.locationrecord': {
            'Meta': {'object_name': 'LocationRecord'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'url'", 'max_length': '80'}),
            'value': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        'hpctardis.partylocation': {
            'Meta': {'object_name': 'PartyLocation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hpctardis.PartyRecord']"}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'url'", 'max_length': '80'}),
            'value': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        'hpctardis.partyrecord': {
            'Meta': {'object_name': 'PartyRecord'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'location': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['hpctardis.LocationRecord']", 'symmetrical': 'False'}),
            'name_family': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name_given': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name_title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        }
    }

    complete_apps = ['hpctardis']
