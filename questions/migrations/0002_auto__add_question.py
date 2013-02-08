# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Question'
        db.create_table('questions_question', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('organisation_type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('choices_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('question', self.gf('django.db.models.fields.TextField')()),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('reporter_name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('reporter_phone', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('reporter_email', self.gf('django.db.models.fields.CharField')(max_length=254, blank=True)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('public_reporter_name', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('preferred_contact_method', self.gf('django.db.models.fields.CharField')(default='email', max_length=100)),
        ))
        db.send_create_signal('questions', ['Question'])


    def backwards(self, orm):
        # Deleting model 'Question'
        db.delete_table('questions_question')


    models = {
        'questions.question': {
            'Meta': {'object_name': 'Question'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'choices_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'organisation_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'preferred_contact_method': ('django.db.models.fields.CharField', [], {'default': "'email'", 'max_length': '100'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public_reporter_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'reporter_email': ('django.db.models.fields.CharField', [], {'max_length': '254', 'blank': 'True'}),
            'reporter_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'reporter_phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        }
    }

    complete_apps = ['questions']