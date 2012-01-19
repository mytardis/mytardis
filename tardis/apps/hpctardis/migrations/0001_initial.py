# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'NameParts'
        db.create_table('hpctardis_nameparts', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
            ('given', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
            ('family', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
            ('suffix', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
        ))
        db.send_create_signal('hpctardis', ['NameParts'])

        # Adding model 'PartyRecord'
        db.create_table('hpctardis_partyrecord', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('type', self.gf('django.db.models.fields.CharField')(default='person', max_length=80)),
            ('partyname', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reverse', to=orm['hpctardis.NameParts'])),
            ('birthdate', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('deathdate', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
        ))
        db.send_create_signal('hpctardis', ['PartyRecord'])

        # Adding model 'PartyLocation'
        db.create_table('hpctardis_partylocation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='url', max_length=80)),
            ('value', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hpctardis.PartyRecord'])),
        ))
        db.send_create_signal('hpctardis', ['PartyLocation'])

        # Adding model 'PartyDescription'
        db.create_table('hpctardis_partydescription', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='', max_length=80)),
            ('value', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hpctardis.PartyRecord'])),
        ))
        db.send_create_signal('hpctardis', ['PartyDescription'])

        # Adding model 'ActivityRecord'
        db.create_table('hpctardis_activityrecord', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ident', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('key', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('type', self.gf('django.db.models.fields.CharField')(default='', max_length=80)),
            ('activityname', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hpctardis.NameParts'])),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal('hpctardis', ['ActivityRecord'])

        # Adding model 'ActivityDescription'
        db.create_table('hpctardis_activitydescription', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='', max_length=80)),
            ('value', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hpctardis.ActivityRecord'])),
        ))
        db.send_create_signal('hpctardis', ['ActivityDescription'])

        # Adding model 'ActivityLocation'
        db.create_table('hpctardis_activitylocation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='url', max_length=80)),
            ('value', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('activity', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hpctardis.ActivityRecord'])),
        ))
        db.send_create_signal('hpctardis', ['ActivityLocation'])

        # Adding model 'ActivityPartyRelation'
        db.create_table('hpctardis_activitypartyrelation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('activity', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hpctardis.ActivityRecord'])),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hpctardis.PartyRecord'])),
            ('relation', self.gf('django.db.models.fields.CharField')(default='isManagedBy', max_length=80)),
        ))
        db.send_create_signal('hpctardis', ['ActivityPartyRelation'])


    def backwards(self, orm):
        
        # Deleting model 'NameParts'
        db.delete_table('hpctardis_nameparts')

        # Deleting model 'PartyRecord'
        db.delete_table('hpctardis_partyrecord')

        # Deleting model 'PartyLocation'
        db.delete_table('hpctardis_partylocation')

        # Deleting model 'PartyDescription'
        db.delete_table('hpctardis_partydescription')

        # Deleting model 'ActivityRecord'
        db.delete_table('hpctardis_activityrecord')

        # Deleting model 'ActivityDescription'
        db.delete_table('hpctardis_activitydescription')

        # Deleting model 'ActivityLocation'
        db.delete_table('hpctardis_activitylocation')

        # Deleting model 'ActivityPartyRelation'
        db.delete_table('hpctardis_activitypartyrelation')


    models = {
        'hpctardis.activitydescription': {
            'Meta': {'object_name': 'ActivityDescription'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hpctardis.ActivityRecord']"}),
            'type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'}),
            'value': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
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
            'activityname': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hpctardis.NameParts']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ident': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'parties': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['hpctardis.PartyRecord']", 'through': "orm['hpctardis.ActivityPartyRelation']", 'symmetrical': 'False'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'})
        },
        'hpctardis.nameparts': {
            'Meta': {'object_name': 'NameParts'},
            'family': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'given': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'})
        },
        'hpctardis.partydescription': {
            'Meta': {'object_name': 'PartyDescription'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hpctardis.PartyRecord']"}),
            'type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'}),
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
            'birthdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'deathdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'partyname': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reverse'", 'to': "orm['hpctardis.NameParts']"}),
            'subject': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'person'", 'max_length': '80'})
        }
    }

    complete_apps = ['hpctardis']
