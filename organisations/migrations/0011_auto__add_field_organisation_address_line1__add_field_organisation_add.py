# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Organisation.address_line1'
        db.add_column('organisations_organisation', 'address_line1',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)

        # Adding field 'Organisation.address_line2'
        db.add_column('organisations_organisation', 'address_line2',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)

        # Adding field 'Organisation.address_line3'
        db.add_column('organisations_organisation', 'address_line3',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)

        # Adding field 'Organisation.city'
        db.add_column('organisations_organisation', 'city',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=50, blank=True),
                      keep_default=False)

        # Adding field 'Organisation.county'
        db.add_column('organisations_organisation', 'county',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=50, blank=True),
                      keep_default=False)

        # Adding field 'Organisation.postcode'
        db.add_column('organisations_organisation', 'postcode',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=10, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Organisation.address_line1'
        db.delete_column('organisations_organisation', 'address_line1')

        # Deleting field 'Organisation.address_line2'
        db.delete_column('organisations_organisation', 'address_line2')

        # Deleting field 'Organisation.address_line3'
        db.delete_column('organisations_organisation', 'address_line3')

        # Deleting field 'Organisation.city'
        db.delete_column('organisations_organisation', 'city')

        # Deleting field 'Organisation.county'
        db.delete_column('organisations_organisation', 'county')

        # Deleting field 'Organisation.postcode'
        db.delete_column('organisations_organisation', 'postcode')


    models = {
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

    complete_apps = ['organisations']