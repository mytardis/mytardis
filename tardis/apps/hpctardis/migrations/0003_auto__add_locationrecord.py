# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'LocationRecord'
        db.create_table('hpctardis_locationrecord', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='url', max_length=80)),
            ('value', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal('hpctardis', ['LocationRecord'])

        # Adding M2M table for field locations on 'PartyRecord'
        db.create_table('hpctardis_partyrecord_locations', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('partyrecord', models.ForeignKey(orm['hpctardis.partyrecord'], null=False)),
            ('locationrecord', models.ForeignKey(orm['hpctardis.locationrecord'], null=False))
        ))
        db.create_unique('hpctardis_partyrecord_locations', ['partyrecord_id', 'locationrecord_id'])

        # Adding M2M table for field locations on 'ActivityRecord'
        db.create_table('hpctardis_activityrecord_locations', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('activityrecord', models.ForeignKey(orm['hpctardis.activityrecord'], null=False)),
            ('locationrecord', models.ForeignKey(orm['hpctardis.locationrecord'], null=False))
        ))
        db.create_unique('hpctardis_activityrecord_locations', ['activityrecord_id', 'locationrecord_id'])


    def backwards(self, orm):
        
        # Deleting model 'LocationRecord'
        db.delete_table('hpctardis_locationrecord')

        # Removing M2M table for field locations on 'PartyRecord'
        db.delete_table('hpctardis_partyrecord_locations')

        # Removing M2M table for field locations on 'ActivityRecord'
        db.delete_table('hpctardis_activityrecord_locations')


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
