# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Question.organisation_type'
        db.delete_column('questions_question', 'organisation_type')

        # Deleting field 'Question.choices_id'
        db.delete_column('questions_question', 'choices_id')


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Question.organisation_type'
        raise RuntimeError("Cannot reverse this migration. 'Question.organisation_type' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Question.choices_id'
        raise RuntimeError("Cannot reverse this migration. 'Question.choices_id' and its values cannot be restored.")

    models = {
        'questions.question': {
            'Meta': {'object_name': 'Question'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'preferred_contact_method': ('django.db.models.fields.CharField', [], {'default': "'email'", 'max_length': '100'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public_reporter_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reporter_email': ('django.db.models.fields.CharField', [], {'max_length': '254', 'blank': 'True'}),
            'reporter_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'reporter_phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['questions']