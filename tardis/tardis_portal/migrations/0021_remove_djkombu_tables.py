from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        conn = db._get_connection()
        tables = conn.introspection.table_names()

        for label, model in orm.models.items():
            if label.split('.')[0] != self.complete_apps[0]:
                continue
            if model._meta.db_table in tables:
                db.delete_table(model._meta.db_table)

    def backwards(self, orm):
        pass

    models = {
        'django.message': {
            'Meta': {
                'object_name': 'Message',
                'db_table': "'djkombu_message'"
            },
            'id': ('django.db.models.fields.AutoField', [],
                   {'primary_key': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {}),
            'queue': ('django.db.models.fields.related.ForeignKey', [],
                      {'related_name': "'messages'",
                       'to': "orm['django.Queue']"}),
            'sent_at': ('django.db.models.fields.DateTimeField', [],
                        {'auto_now_add': 'True', 'null': 'True',
                         'db_index': 'True',
                         'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [],
                        {'default': 'True', 'db_index': 'True'})
        },
        'django.queue': {
            'Meta':
            {'object_name': 'Queue', 'db_table': "'djkombu_queue'"},
            'id': ('django.db.models.fields.AutoField', [],
                   {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [],
                     {'unique': 'True', 'max_length': '200'})}}

    complete_apps = ['django']
