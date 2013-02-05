# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Problem'
        db.create_table('problems_problem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('organisation_type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('organisation_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('reporter_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('reporter_phone', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('reporter_email', self.gf('django.db.models.fields.CharField')(max_length=254)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('public_reporter_name', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('problems', ['Problem'])


    def backwards(self, orm):
        # Deleting model 'Problem'
        db.delete_table('problems_problem')


    models = {
        'problems.problem': {
            'Meta': {'object_name': 'Problem'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'organisation_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'organisation_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public_reporter_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reporter_email': ('django.db.models.fields.CharField', [], {'max_length': '254'}),
            'reporter_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'reporter_phone': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['problems']