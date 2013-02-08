# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.rename_column('questions_question', 'question', 'description')

    def backwards(self, orm):
        db.rename_column('questions_question', 'description', 'question')

    models = {
        'questions.question': {
            'Meta': {'object_name': 'Question'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'choices_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'organisation_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'preferred_contact_method': ('django.db.models.fields.CharField', [], {'default': "'email'", 'max_length': '100'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public_reporter_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reporter_email': ('django.db.models.fields.CharField', [], {'max_length': '254', 'blank': 'True'}),
            'reporter_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'reporter_phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        }
    }

    complete_apps = ['questions']