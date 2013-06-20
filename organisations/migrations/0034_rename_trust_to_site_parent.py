# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        """Rename Trust to SiteParent, and adjust the relations as necessary"""

        # Rename the Trust table
        db.rename_table('organisations_trust', 'organisations_siteparent')
        db.send_create_signal('organisations', ['SiteParent'])

        # Rename the M2M table for field users on SiteParent
        old_users_m2m_name = db.shorten_name('organisations_trust_users')
        new_users_m2m_name = db.shorten_name('organisations_siteparent_users')
        db.rename_table(old_users_m2m_name, new_users_m2m_name)
        # Rename field 'organisations_siteparent_users.trust_id' to 'siteparent_id'
        db.rename_column(new_users_m2m_name, 'trust_id', 'siteparent_id')
        # Changing field 'organisations_siteparent_users.siteparent_id' to point to SiteParent
        db.alter_column(new_users_m2m_name, 'siteparent_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.SiteParent']))

        # Rename the M2M table for field regulators on SiteParent
        old_regulators_m2m_name = db.shorten_name('organisations_trust_regulators')
        new_regulators_m2m_name = db.shorten_name('organisations_siteparent_regulators')
        db.rename_table(old_regulators_m2m_name, new_regulators_m2m_name)
        # Rename field 'organisations_siteparent_regulators.trust_id' to 'siteparent_id'
        db.rename_column(new_regulators_m2m_name, 'trust_id', 'siteparent_id')
        # Changing field 'organisations_siteparent_regulators.siteparent_id' to point to SiteParent
        db.alter_column(new_regulators_m2m_name, 'siteparent_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.SiteParent']))

        # Rename field 'Organisation.trust to Organisation.parent'
        db.rename_column('organisations_organisation', 'trust_id', 'parent_id')
        # Changing field 'organisations_organisation.parent_id' to point to SiteParent
        db.alter_column('organisations_organisation', 'parent_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.SiteParent']))


    def backwards(self, orm):
        """Rename SiteParent to Trust, and adjust the relations as necessary"""

        # Rename the SiteParent table
        db.rename_table('organisations_siteparent', 'organisations_trust')
        db.send_create_signal('organisations', ['Trust'])

        # Rename the M2M table for field users on Trust
        old_users_m2m_name = db.shorten_name('organisations_siteparent_users')
        new_users_m2m_name = db.shorten_name('organisations_trust_users')
        db.rename_table(old_users_m2m_name, new_users_m2m_name)
        # Rename field 'organisations_trust_users.siteparent_id' to 'trust_id'
        db.rename_column(new_users_m2m_name, 'siteparent_id', 'trust_id')
        # Changing field 'organisations_trust_users.trust_id' to point to Trust
        db.alter_column(new_users_m2m_name, 'trust_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.Trust']))

        # Rename the M2M table for field regulators on Trust
        # Half of this should have been done in 0033, but oh well
        old_regulators_m2m_name = db.shorten_name('organisations_siteparent_regulators')
        new_regulators_m2m_name = db.shorten_name('organisations_trust_regulators')
        db.rename_table(old_regulators_m2m_name, new_regulators_m2m_name)
        # Rename field 'organisations_trust_ccgs.siteparent_id' to 'trust_id'
        db.rename_column(new_regulators_m2m_name, 'siteparent_id', 'trust_id')
        # Changing field 'organisations_trust_ccgs.trust_id' to point to Trust
        db.alter_column(new_regulators_m2m_name, 'trust_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.Trust']))

        # Rename field 'Organisation.parent to Organisation.trust'
        db.rename_column('organisations_organisation', 'parent_id', 'trust_id')
        # Changing field 'organisations_organisation.trust_id' to point to SiteParent
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
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'organisations'", 'to': "orm['organisations.SiteParent']"}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'postcode': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'organisations.regulator': {
            'Meta': {'object_name': 'Regulator'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro_email_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'regulators'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
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
        'organisations.siteparent': {
            'Meta': {'object_name': 'SiteParent'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'blank': 'True'}),
            'escalation_regulator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'escalation_site_parents'", 'to': "orm['organisations.Regulator']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro_email_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'regulators': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'site_parents'", 'symmetrical': 'False', 'to': "orm['organisations.Regulator']"}),
            'secondary_email': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'site_parents'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
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