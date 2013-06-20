# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        """Rename CCG to Regulator, and adjust the relations as necessary"""

        # Rename the CCG table
        db.rename_table('organisations_ccg', 'organisations_regulator')
        db.send_create_signal('organisations', ['Regulator'])

        # Rename the M2M table for field users on CCG
        old_users_m2m_name = db.shorten_name('organisations_ccg_users')
        new_users_m2m_name = db.shorten_name('organisations_regulator_users')
        db.rename_table(old_users_m2m_name, new_users_m2m_name)
        # Rename field 'organisations_regulator_users.ccg_id' to 'regulator_id'
        db.rename_column(new_users_m2m_name, 'ccg_id', 'regulator_id')
        # Changing field 'organisations_regulator_users.regulator_id' to point to Regulator
        db.alter_column(new_users_m2m_name, 'regulator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.Regulator']))

        # Rename the M2M table for field regulators on Trust
        old_regulators_m2m_name = db.shorten_name('organisations_trust_ccgs')
        new_regulators_m2m_name = db.shorten_name('organisations_trust_regulators')
        db.rename_table(old_regulators_m2m_name, new_regulators_m2m_name)
        # Rename field 'organisations_trust_regulators.ccg_id' to 'regulator_id'
        db.rename_column(new_regulators_m2m_name, 'ccg_id', 'regulator_id')
        # Changing field 'organisations_trust_regulators.regulator_id' to point to Regulator
        db.alter_column(new_regulators_m2m_name, 'regulator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.Regulator']))

        # Rename field 'Trust.escalation_ccg' to 'Trust.escalation_regulator'
        db.rename_column('organisations_trust', 'escalation_ccg_id', 'escalation_regulator_id')
        # Changing field 'Trust.escalation_regulator' to point to Regulator
        db.alter_column('organisations_trust', 'escalation_regulator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.Regulator']))


    def backwards(self, orm):
        """Rename Regulator to CCG, and adjust relations as necessary"""

        # Rename the Regulator table
        db.rename_table('organisations_regulator', 'organisations_ccg')
        db.send_create_signal('organisations', ['CCG'])

        # Rename the M2M table for field users on Regulator
        old_users_m2m_name = db.shorten_name('organisations_regulator_users')
        new_users_m2m_name = db.shorten_name('organisations_ccg_users')
        db.rename_table(old_users_m2m_name, new_users_m2m_name)
        # Rename field 'organisations_regulator_users.regulator_id' to 'ccg_id'
        db.rename_column(new_users_m2m_name, 'regulator_id', 'ccg_id')
        # Changing field 'organisations_regulator_users.ccg_id' to point to CCG
        db.alter_column(new_users_m2m_name, 'ccg_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.CCG']))

        # Rename the M2M table for field regulators on Trust
        old_regulators_m2m_name = db.shorten_name('organisations_trust_regulators')
        new_regulators_m2m_name = db.shorten_name('organisations_trust_ccgs')
        db.rename_table(old_regulators_m2m_name, new_regulators_m2m_name)
        # Rename field 'organisations_trust_ccgs.regulator_id' to 'ccg_id'
        db.rename_column(new_regulators_m2m_name, 'regulator_id', 'ccg_id')
        # Changing field 'organisations_trust_ccgs.ccg_id' to point to CCG
        db.alter_column(new_regulators_m2m_name, 'ccg_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.CCG']))

        # Rename field 'Trust.escalation_regulator' to 'Trust.escalation_ccg'
        db.rename_column('organisations_trust', 'escalation_regulator_id', 'escalation_ccg_id')
        # Changing field 'Trust.escalation_ccg'
        db.alter_column('organisations_trust', 'escalation_ccg_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisations.CCG']))


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
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'postcode': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'trust': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'organisations'", 'to': "orm['organisations.Trust']"})
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
        'organisations.superuserlogentry': {
            'Meta': {'object_name': 'SuperuserLogEntry'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'superuser_access_logs'", 'to': "orm['auth.User']"})
        },
        'organisations.trust': {
            'Meta': {'object_name': 'Trust'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'blank': 'True'}),
            'escalation_regulator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'escalation_trusts'", 'to': "orm['organisations.Regulator']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro_email_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'regulators': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'trusts'", 'symmetrical': 'False', 'to': "orm['organisations.Regulator']"}),
            'secondary_email': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'trusts'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['organisations']