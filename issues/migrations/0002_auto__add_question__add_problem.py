# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Question'
        db.create_table('issues_question', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('organisation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.Organisation'])),
            ('service', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.Service'], null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('reporter_name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('reporter_phone', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('reporter_email', self.gf('django.db.models.fields.CharField')(max_length=254, blank=True)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('public_reporter_name', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('preferred_contact_method', self.gf('django.db.models.fields.CharField')(default='email', max_length=100)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('category', self.gf('django.db.models.fields.CharField')(default='general', max_length=100)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('issues', ['Question'])

        # Adding model 'Problem'
        db.create_table('issues_problem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('organisation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.Organisation'])),
            ('service', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.Service'], null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('reporter_name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('reporter_phone', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('reporter_email', self.gf('django.db.models.fields.CharField')(max_length=254, blank=True)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('public_reporter_name', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('preferred_contact_method', self.gf('django.db.models.fields.CharField')(default='email', max_length=100)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('category', self.gf('django.db.models.fields.CharField')(default='other', max_length=100)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('issues', ['Problem'])


    def backwards(self, orm):
        # Deleting model 'Question'
        db.delete_table('issues_question')

        # Deleting model 'Problem'
        db.delete_table('issues_problem')


    models = {
        'issues.problem': {
            'Meta': {'object_name': 'Problem'},
            'category': ('django.db.models.fields.CharField', [], {'default': "'other'", 'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['organisations.Organisation']"}),
            'preferred_contact_method': ('django.db.models.fields.CharField', [], {'default': "'email'", 'max_length': '100'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public_reporter_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reporter_email': ('django.db.models.fields.CharField', [], {'max_length': '254', 'blank': 'True'}),
            'reporter_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'reporter_phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['organisations.Service']", 'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'issues.question': {
            'Meta': {'object_name': 'Question'},
            'category': ('django.db.models.fields.CharField', [], {'default': "'general'", 'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['organisations.Organisation']"}),
            'preferred_contact_method': ('django.db.models.fields.CharField', [], {'default': "'email'", 'max_length': '100'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public_reporter_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reporter_email': ('django.db.models.fields.CharField', [], {'max_length': '254', 'blank': 'True'}),
            'reporter_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'reporter_phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['organisations.Service']", 'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'organisations.organisation': {
            'Meta': {'object_name': 'Organisation'},
            'choices_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'ods_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8', 'db_index': 'True'}),
            'organisation_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {})
        },
        'organisations.service': {
            'Meta': {'unique_together': "(('service_code', 'organisation'),)", 'object_name': 'Service'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'services'", 'to': "orm['organisations.Organisation']"}),
            'service_code': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['issues']