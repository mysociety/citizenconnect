# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Problem.organisation_id'
        db.delete_column('problems_problem', 'organisation_id')

        # Adding field 'Problem.choices_id'
        db.add_column('problems_problem', 'choices_id',
                      self.gf('django.db.models.fields.IntegerField')(default=None, db_index=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Problem.organisation_id'
        db.add_column('problems_problem', 'organisation_id',
                      self.gf('django.db.models.fields.IntegerField')(default=None, db_index=True),
                      keep_default=False)

        # Deleting field 'Problem.choices_id'
        db.delete_column('problems_problem', 'choices_id')


    models = {
        'problems.problem': {
            'Meta': {'object_name': 'Problem'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'choices_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'organisation_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public_reporter_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reporter_email': ('django.db.models.fields.CharField', [], {'max_length': '254'}),
            'reporter_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'reporter_phone': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['problems']