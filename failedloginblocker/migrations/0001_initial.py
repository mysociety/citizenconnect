# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'FailedAttempt'
        db.create_table('failedloginblocker_failedattempt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('failures', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('failedloginblocker', ['FailedAttempt'])


    def backwards(self, orm):
        # Deleting model 'FailedAttempt'
        db.delete_table('failedloginblocker_failedattempt')


    models = {
        'failedloginblocker.failedattempt': {
            'Meta': {'ordering': "['-timestamp']", 'object_name': 'FailedAttempt'},
            'failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['failedloginblocker']