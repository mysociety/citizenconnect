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
        self.old_stdout = sys.stderr
        sys.stdout = DevNull()

    def tearDown(self):
        sys.stdout = self.old_stdout

    def test_happy_path(self):

        call_command('load_ccgs_from_spreadsheet', 'organisations/tests/samples/ccgs.csv')
        self.assertEqual(CCG.objects.count(), 3)

        call_command('load_trusts_from_spreadsheet', 'organisations/tests/samples/trusts.csv')
        self.assertEqual(Trust.objects.count(), 3)
        self.assertEqual(CCG.objects.get(name="Ascot CCG").trusts.count(), 2)
        self.assertEqual(CCG.objects.get(name="Banbridge CCG").trusts.count(), 2)
        self.assertEqual(CCG.objects.get(name="Chucklemere CCG").trusts.count(), 1)


        call_command('load_organisations_from_spreadsheet', 'organisations/tests/samples/organisations.csv')
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
        call_command('load_ccgs_from_spreadsheet', 'organisations/tests/samples/ccgs.csv')
        call_command('load_trusts_from_spreadsheet', 'organisations/tests/samples/trusts.csv')

        self.assertEqual(User.objects.count(), 0)
        call_command('load_trust_users_from_spreadsheet', 'organisations/tests/samples/trust_users.csv')
        self.assertEqual(User.objects.count(), 3)
        call_command('load_ccg_users_from_spreadsheet', 'organisations/tests/samples/ccg_users.csv')
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
