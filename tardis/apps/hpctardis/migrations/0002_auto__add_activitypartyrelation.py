# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ActivityPartyRelation'
        db.create_table('hpctardis_activitypartyrelation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('activity', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hpctardis.ActivityRecord'])),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hpctardis.PartyRecord'])),
            ('relation', self.gf('django.db.models.fields.CharField')(default='isManagedBy', max_length=80)),
        ))
        db.send_create_signal('hpctardis', ['ActivityPartyRelation'])


    def backwards(self, orm):
        
        # Deleting model 'ActivityPartyRelation'
        db.delete_table('hpctardis_activitypartyrelation')


    models = {
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
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'parties': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['hpctardis.PartyRecord']", 'through': "orm['hpctardis.ActivityPartyRelation']", 'symmetrical': 'False'}),
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
