# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        """Rename Trust to OrganisationParent, and adjust the relations as necessary"""

        # Rename the Trust table to OrganisationParent
        db.rename_table('organisations_trust', 'organisations_organisationparent')
        db.send_create_signal('organisations', ['OrganisationParent'])

        # Rename the M2M table for field users on OrganisationParent
        old_users_m2m_name = db.shorten_name('organisations_trust_users')
        new_users_m2m_name = db.shorten_name('organisations_organisationparent_users')
        db.rename_table(old_users_m2m_name, new_users_m2m_name)
        # Rename field 'organisations_organisationparent_users.trust_id' to 'organisationparent_id'
        db.rename_column(new_users_m2m_name, 'trust_id', 'organisationparent_id')
        # Changing field 'organisations_organisationparent_users.organisationparent_id' to point to OrganisationParent
        db.alter_column(new_users_m2m_name, 'organisationparent_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.OrganisationParent']))

        # Rename the M2M table for field ccgs on OrganisationParent
        old_ccgs_m2m_name = db.shorten_name('organisations_trust_ccgs')
        new_ccgs_m2m_name = db.shorten_name('organisations_organisationparent_ccgs')
        db.rename_table(old_ccgs_m2m_name, new_ccgs_m2m_name)
        # Rename field 'organisations_organisationparent_ccgs.trust_id' to 'organisationparent_id'
        db.rename_column(new_ccgs_m2m_name, 'trust_id', 'organisationparent_id')
        # Changing field 'organisations_organisationparent_ccgs.organisationparent_id' to point to OrganisationParent
        db.alter_column(new_ccgs_m2m_name, 'organisationparent_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.OrganisationParent']))

        # Changing field 'organisations_organisation.trust_id' to point to OrganisationParent
        db.alter_column('organisations_organisation', 'trust_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.OrganisationParent']))


    def backwards(self, orm):
        """Rename OrganisationParent to Trust, and adjust the relations as necessary"""

        # Rename the OrganisationParent table to Trust
        db.rename_table('organisations_organisationparent', 'organisations_trust')
        db.send_create_signal('organisations', ['Trust'])

        # Rename the M2M table for field users on Trust
        old_users_m2m_name = db.shorten_name('organisations_organisationparent_users')
        new_users_m2m_name = db.shorten_name('organisations_trust_users')
        db.rename_table(old_users_m2m_name, new_users_m2m_name)
        # Rename field 'organisations_trust_users.organisationparent_id' to 'trust_id'
        db.rename_column(new_users_m2m_name, 'organisationparent_id', 'trust_id')
        # Changing field 'organisations_trust_users.trust_id' to point to Trust
        db.alter_column(new_users_m2m_name, 'trust_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.Trust']))

        # Rename the M2M table for field ccgs on Trust
        old_ccgs_m2m_name = db.shorten_name('organisations_organisationparent_ccgs')
        new_ccgs_m2m_name = db.shorten_name('organisations_trust_ccgs')
        db.rename_table(old_ccgs_m2m_name, new_ccgs_m2m_name)
        # Rename field 'organisations_trust_ccgs.organisationparent_id' to 'trust_id'
        db.rename_column(new_ccgs_m2m_name, 'trust_id', 'organisationparent_id')
        # Changing field 'organisations_trust_ccgs.trust_id' to point to Trust
        db.alter_column(new_ccgs_m2m_name, 'trust_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.Trust']))

        # Changing field 'organisations_organisation.trust_id' to point to Trust
        db.alter_column('organisations_organisation', 'trust_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.Trust']))

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
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'blank': 'True'}),
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
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'name_metaphone': ('django.db.models.fields.TextField', [], {}),
            'ods_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8', 'db_index': 'True'}),
            'organisation_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'postcode': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'trust': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'organisations'", 'to': "orm['organisations.OrganisationParent']"})
        },
        'organisations.organisationparent': {
            'Meta': {'object_name': 'OrganisationParent'},
            'ccgs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'trusts'", 'symmetrical': 'False', 'to': "orm['organisations.CCG']"}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'blank': 'True'}),
            'escalation_ccg': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'escalation_trusts'", 'to': "orm['organisations.CCG']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro_email_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'secondary_email': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'trusts'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
        },
        'organisations.service': {
            'Meta': {'unique_together': "(('service_code', 'organisation'),)", 'object_name': 'Service'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'services'", 'to': "orm['organisations.Organisation']"}),
            'service_code': ('django.db.models.fields.TextField', [], {'db_index': 'True'})
        },
        'organisations.superuserlogentry': {
            'Meta': {'object_name': 'SuperuserLogEntry'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'superuser_access_logs'", 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['organisations']