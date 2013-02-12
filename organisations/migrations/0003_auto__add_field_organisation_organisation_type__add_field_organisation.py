# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Organisation.organisation_type'
        db.add_column('organisations_organisation', 'organisation_type',
                      self.gf('django.db.models.fields.CharField')(default='hospitals', max_length=100),
                      keep_default=False)

        # Adding field 'Organisation.choices_id'
        db.add_column('organisations_organisation', 'choices_id',
                      self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Organisation.organisation_type'
        db.delete_column('organisations_organisation', 'organisation_type')

        # Deleting field 'Organisation.choices_id'
        db.delete_column('organisations_organisation', 'choices_id')


    models = {
        'organisations.organisation': {
            'Meta': {'object_name': 'Organisation'},
            'choices_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {}),
            'lon': ('django.db.models.fields.FloatField', [], {}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'organisation_type': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['organisations']
