# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'Rating', fields ['created']
        db.create_index('reviews_display_rating', ['created'])

        # Adding index on 'Review', fields ['created']
        db.create_index('reviews_display_review', ['created'])


    def backwards(self, orm):
        # Removing index on 'Review', fields ['created']
        db.delete_index('reviews_display_review', ['created'])

        # Removing index on 'Rating', fields ['created']
        db.delete_index('reviews_display_rating', ['created'])


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'organisations.ccg': {
            'Meta': {'object_name': 'CCG'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '254'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro_email_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'ccgs'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
        },
        'organisations.organisation': {
            'Meta': {'object_name': 'Organisation'},
            'address_line1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'address_line2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'address_line3': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'average_recommendation_rating': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'choices_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'county': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'name_metaphone': ('django.db.models.fields.TextField', [], {}),
            'ods_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '12', 'db_index': 'True'}),
            'organisation_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'organisations'", 'to': "orm['organisations.OrganisationParent']"}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'postcode': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'organisations.organisationparent': {
            'Meta': {'object_name': 'OrganisationParent'},
            'ccgs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organisation_parents'", 'symmetrical': 'False', 'to': "orm['organisations.CCG']"}),
            'choices_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '254'}),
            'escalation_ccg': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'escalation_organisation_parents'", 'to': "orm['organisations.CCG']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro_email_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'secondary_email': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organisation_parents'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
        },
        'reviews_display.rating': {
            'Meta': {'object_name': 'Rating'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'review': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ratings'", 'to': "orm['reviews_display.Review']"}),
            'score': ('django.db.models.fields.IntegerField', [], {})
        },
        'reviews_display.review': {
            'Meta': {'unique_together': "(('api_posting_id', 'api_postingorganisationid'),)", 'object_name': 'Review'},
            'api_category': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'api_posting_id': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'api_postingorganisationid': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'api_published': ('django.db.models.fields.DateTimeField', [], {}),
            'api_updated': ('django.db.models.fields.DateTimeField', [], {}),
            'author_display_name': ('django.db.models.fields.TextField', [], {}),
            'content': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'content_improved': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'content_liked': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_reply_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'replies'", 'null': 'True', 'to': "orm['reviews_display.Review']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'organisations': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'reviews'", 'symmetrical': 'False', 'to': "orm['organisations.Organisation']"}),
            'title': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['reviews_display']