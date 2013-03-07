# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Question.moderated'
        db.add_column('issues_question', 'moderated',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Problem.moderated'
        db.add_column('issues_problem', 'moderated',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Question.moderated'
        db.delete_column('issues_question', 'moderated')

        # Deleting field 'Problem.moderated'
        db.delete_column('issues_problem', 'moderated')


    models = {
        'issues.problem': {
            'Meta': {'object_name': 'Problem'},
            'category': ('django.db.models.fields.CharField', [], {'default': "'other'", 'max_length': '100', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'happy_outcome': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'happy_service': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'moderated': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['organisations.Organisation']"}),
            'preferred_contact_method': ('django.db.models.fields.CharField', [], {'default': "'email'", 'max_length': '100'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public_reporter_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'publication_status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'reporter_email': ('django.db.models.fields.CharField', [], {'max_length': '254', 'blank': 'True'}),
            'reporter_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'reporter_phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['organisations.Service']", 'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'time_to_acknowledge': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'time_to_address': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        'issues.question': {
            'Meta': {'object_name': 'Question'},
            'category': ('django.db.models.fields.CharField', [], {'default': "'general'", 'max_length': '100', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'moderated': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'postcode': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'preferred_contact_method': ('django.db.models.fields.CharField', [], {'default': "'email'", 'max_length': '100'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public_reporter_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'publication_status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'reporter_email': ('django.db.models.fields.CharField', [], {'max_length': '254', 'blank': 'True'}),
            'reporter_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'reporter_phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'})
        },
        'organisations.organisation': {
            'Meta': {'object_name': 'Organisation'},
            'address_line1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'address_line2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'address_line3': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'choices_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'county': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'ods_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8', 'db_index': 'True'}),
            'organisation_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'postcode': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'organisations.service': {
            'Meta': {'unique_together': "(('service_code', 'organisation'),)", 'object_name': 'Service'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'services'", 'to': "orm['organisations.Organisation']"}),
            'service_code': ('django.db.models.fields.TextField', [], {'db_index': 'True'})
        }
    }

    complete_apps = ['issues']