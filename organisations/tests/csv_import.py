import sys
import re
import os
import urllib
import shutil
import tempfile

from mock import MagicMock

from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.contrib.auth.models import User
from django.forms.models import model_to_dict

from ..models import Organisation, OrganisationParent, CCG

import organisations
from organisations import auth


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
        self.trusts_csv        = csv_dir + 'organisation_parents.csv'
        self.organisations_csv = csv_dir + 'organisations.csv'
        self.other_users_csv   = csv_dir + 'other_users.csv'
        self.ccg_users_csv     = csv_dir + 'ccg_users.csv'
        self.trust_users_csv   = csv_dir + 'organisation_parent_users.csv'

        # Sample image file
        sample_hospital_image = os.path.join(
            os.path.abspath(organisations.__path__[0]),
            'tests',
            'fixtures',
            'sample-hospital-image.jpg'
        )
        # Copy it to tempfile because the import expects a tempfile to delete
        (handle, filename) = tempfile.mkstemp(".jpg")
        self.temp_hospital_image = filename
        shutil.copyfile(sample_hospital_image, self.temp_hospital_image)

        # Mock urllib.urlretrieve so that our command can call it
        self._original_urlretrieve = urllib.urlopen
        # urlretrieve returns a tuple of a file and some headers
        urllib.urlretrieve = MagicMock(return_value=(self.temp_hospital_image, None))

    def tearDown(self):
        # Undo the mocking of urlretrieve
        urllib.urlretrieve = self._original_urlretrieve
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

        # Wipe the temporary files
        if(os.path.exists(self.temp_hospital_image)):
            os.remove(self.temp_hospital_image)

    def test_organisations(self):

        call_command('load_ccgs_from_csv', self.ccgs_csv)
        self.assertEqual(CCG.objects.count(), 3)

        call_command('load_organisation_parents_from_csv', self.trusts_csv)
        self.assertEqual(OrganisationParent.objects.count(), 3)
        self.assertEqual(CCG.objects.get(name="Ascot CCG").organisation_parents.count(), 2)
        self.assertEqual(CCG.objects.get(name="Banbridge CCG").organisation_parents.count(), 2)
        self.assertEqual(CCG.objects.get(name="Chucklemere CCG").organisation_parents.count(), 1)

        call_command('load_organisations_from_csv', self.organisations_csv)
        self.assertEqual(Organisation.objects.count(), 3)
        self.assertEqual(OrganisationParent.objects.get(name="Ascot North Trust").organisations.count(), 2)
        self.assertEqual(OrganisationParent.objects.get(name="Ascot South Trust").organisations.count(), 1)
        self.assertEqual(OrganisationParent.objects.get(name="Banbridge North Trust").organisations.count(), 0)

        # Now check that the correct data has been loaded

        ccg = CCG.objects.get(name="Ascot CCG")
        self.assertEqual(
            model_to_dict(ccg),
            {
                'code': '07A',
                'email': 'ascot@example.com',
                'id': ccg.id,
                'name': 'Ascot CCG',
                'users': [],
            }
        )

        org_parent = OrganisationParent.objects.get(name="Ascot North Trust")
        self.assertEqual(
            model_to_dict(org_parent, exclude=['ccgs']),
            {
                'code': 'AN1',
                'choices_id': 1234,
                'email': 'an-trust@example.com',
                'escalation_ccg': ccg.id,
                'id': org_parent.id,
                'name': 'Ascot North Trust',
                'secondary_email': 'an-trust-backup@example.com',
                'users': [],
            }
        )
        self.assertEqual(
            [result.code for result in org_parent.ccgs.order_by('code')],
            ['07A', '07B', '07C'],
        )

        organisation = Organisation.objects.get(name="Ascot North Hospital 1")
        org_dict = model_to_dict(organisation)
        del org_dict['point']  # Tedious to test

        # Test the image was added
        image_filename = org_dict.get('image').url
        image_filename_regex = re.compile('organisation_images/\w{2}/\w{2}/[0-9a-f]{32}.jpg', re.I)
        self.assertRegexpMatches(image_filename, image_filename_regex)
        del org_dict['image']

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
                'parent': org_parent.id,
            }
        )

    def test_user_imports(self):
        # Load up some test CCGs and organisation parents
        call_command('load_ccgs_from_csv', self.ccgs_csv)
        call_command('load_organisation_parents_from_csv', self.trusts_csv)

        self.assertEqual(User.objects.count(), 0)
        call_command('load_organisation_parent_users_from_csv', self.trust_users_csv)
        self.assertEqual(User.objects.count(), 3)
        call_command('load_ccg_users_from_csv', self.ccg_users_csv)
        self.assertEqual(User.objects.count(), 6)

        org_parent = OrganisationParent.objects.get(name='Ascot North Trust')
        self.assertEqual(org_parent.users.count(), 2)  # has two users in CSV
        self.assertEqual(OrganisationParent.objects.get(name='Ascot South Trust').users.count(), 1)

        ccg = CCG.objects.get(name='Ascot CCG')
        self.assertEqual(ccg.users.count(), 1)

        # test that users' passwords _ARE_ usable - if not usable then
        # the password cannot be reset. See #689
        for user in [ccg.users.all()[0], org_parent.users.all()[0]]:
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
        call_command('load_other_users_from_csv', self.other_users_csv)

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
        # test that users' passwords _ARE_ usable - if not usable then
        # the password cannot be reset. See #689 and #1084
        emails = [
            'spreadsheetsuper@example.com',
            'spreadsheetcasehandler@example.com',
            'spreadsheetcasemod@example.com',
            'spreadsheetccc@example.com'
        ]
        for email in emails:
            user = User.objects.get(email=email)
            self.assertTrue(user.password)
            self.assertTrue(user.has_usable_password())

    def test_image_retrieval_errors(self):
        # Mock urlretrieve to throw an error
        urllib.urlretrieve.side_effect = Exception("Boom!")

        # Load the data in
        call_command('load_ccgs_from_csv', self.ccgs_csv)
        call_command('load_organisation_parents_from_csv', self.trusts_csv)
        call_command('load_organisations_from_csv', self.organisations_csv)

        # Check it worked, but we have no image
        self.assertEqual(Organisation.objects.count(), 3)
        org = Organisation.objects.get(name="Ascot North Hospital 1")
        self.assertFalse(bool(org.image))

        urllib.urlretrieve.side_effect = None
