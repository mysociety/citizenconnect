import logging
import os
import sys
from StringIO import StringIO

from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.models import User
from django.forms.models import model_to_dict

from ..models import Organisation, Trust, CCG

from organisations import auth
from issues.models import Problem


class DevNull(object):
    def write(self, data):
        pass


class CsvImportTests(TestCase):

    # Commands are chatty. Consume STDOUT
    def setUp(self):
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = DevNull()
        sys.stderr = DevNull()

        # Paths to the various sample CSV files
        csv_dir = 'documentation/csv_samples/'
        self.ccgs_csv          = csv_dir + 'ccgs.csv'
        self.trusts_csv        = csv_dir + 'trusts.csv'
        self.organisations_csv = csv_dir + 'organisations.csv'
        self.other_users_csv   = csv_dir + 'other_users.csv'
        self.ccg_users_csv     = csv_dir + 'ccg_users.csv'
        self.trust_users_csv   = csv_dir + 'trust_users.csv'


    def tearDown(self):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

    def test_organisations(self):

        call_command('load_ccgs_from_csv', self.ccgs_csv)
        self.assertEqual(CCG.objects.count(), 3)

        call_command('load_trusts_from_csv', self.trusts_csv)
        self.assertEqual(Trust.objects.count(), 3)
        self.assertEqual(CCG.objects.get(name="Ascot CCG").trusts.count(), 2)
        self.assertEqual(CCG.objects.get(name="Banbridge CCG").trusts.count(), 2)
        self.assertEqual(CCG.objects.get(name="Chucklemere CCG").trusts.count(), 1)


        call_command('load_organisations_from_csv', self.organisations_csv)
        self.assertEqual(Organisation.objects.count(), 3)
        self.assertEqual(Trust.objects.get(name="Ascot North Trust").organisations.count(), 2)
        self.assertEqual(Trust.objects.get(name="Ascot South Trust").organisations.count(), 1)
        self.assertEqual(Trust.objects.get(name="Banbridge North Trust").organisations.count(), 0)

        # Now check that the correct data has been loaded

        ccg = CCG.objects.get(name="Ascot CCG")
        self.assertEqual(
            model_to_dict(ccg),
            {   'code': '07A',
                'email': 'ascot@example.com',
                'id': ccg.id,
                'name': 'Ascot CCG',
                'users': [],
            }
        )

        trust = Trust.objects.get(name="Ascot North Trust")
        self.assertEqual(
            model_to_dict(trust, exclude=['ccgs']),
            {
                'code': 'AN1',
                'email': 'an-trust@example.com',
                'escalation_ccg': ccg.id,
                'id': trust.id,
                'name': 'Ascot North Trust',
                'secondary_email': 'an-trust-backup@example.com',
                'users': [],
            }
        )
        self.assertEqual(
            [ ccg.code for ccg in trust.ccgs.order_by('code') ],
            [ '07A', '07B', '07C' ],
        )

        organisation = Organisation.objects.get(name="Ascot North Hospital 1")
        org_dict = model_to_dict(organisation)
        del org_dict['point'] # Tedious to test
        self.assertEqual(
            org_dict,
            {
                'address_line1': 'Foo Street',
                'address_line2': '',
                'address_line3': '',
                'average_recommendation_rating': None,
                'choices_id': 11111,
                'city': 'London ',
                'county': 'Greater London',
                'id': organisation.id,
                'name': 'Ascot North Hospital 1',
                'ods_code': 'ANH1',
                'organisation_type': 'hospitals',
                'postcode': 'NW8 7BT ',
                'trust': trust.id
            }
        )

    def test_user_imports(self):
        # Load up some test CCGs and trusts
        call_command('load_ccgs_from_csv', self.ccgs_csv)
        call_command('load_trusts_from_csv', self.trusts_csv)

        self.assertEqual(User.objects.count(), 0)
        call_command('load_trust_users_from_csv', self.trust_users_csv)
        self.assertEqual(User.objects.count(), 3)
        call_command('load_ccg_users_from_csv', self.ccg_users_csv)
        self.assertEqual(User.objects.count(), 6)

        trust = Trust.objects.get(name='Ascot North Trust')
        self.assertEqual(trust.users.count(), 2) # has two users in CSV
        self.assertEqual(Trust.objects.get(name='Ascot South Trust').users.count(), 1)

        ccg = CCG.objects.get(name='Ascot CCG')
        self.assertEqual(ccg.users.count(), 1)

        # test that users' passwords _ARE_ usable - if not usable then
        # the password cannot be reset. See #689
        for user in [ccg.users.all()[0], trust.users.all()[0]]:
            self.assertTrue(user.has_usable_password())

        self.assertEqual(len(mail.outbox), 6)
        last_mail = mail.outbox[0]

        self.assertEqual(last_mail.subject, 'Welcome to Care Connect')
        self.assertIn("You're receiving this e-mail because an account has been created for you on the  Care Connect website.", last_mail.body)


    def expect_groups(self, email, expected_groups):
        user = User.objects.get(email=email)
        self.assertTrue(auth.user_in_groups(user, expected_groups))
        other_groups = [group for group in auth.ALL_GROUPS if not group in expected_groups]
        for group in other_groups:
            self.assertFalse(auth.user_in_group(user, group))

    def test_other_users(self):
        call_command('load_users_from_csv', self.other_users_csv)

        self.expect_groups('spreadsheetsuper@example.com', [auth.NHS_SUPERUSERS])
        self.expect_groups('spreadsheetcasehandler@example.com', [auth.CASE_HANDLERS])
        self.expect_groups('spreadsheetcasemod@example.com', [auth.CASE_HANDLERS,
                                                              auth.SECOND_TIER_MODERATORS])
        self.expect_groups('spreadsheetccc@example.com', [auth.CUSTOMER_CONTACT_CENTRE])
        bad_row_users = User.objects.filter(email='spreadsheetbadrow@example.com')
        # Should not have created a user if the groups are ambiguous
        self.assertEqual(0, len(bad_row_users))
        # Should have sent an email to each created user
        self.assertEqual(len(mail.outbox), 4)
        first_email = mail.outbox[0]
        expected_text = "You're receiving this e-mail because an account has been created"
        self.assertTrue(expected_text in first_email.body)
