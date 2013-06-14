import logging
import os
import sys
from StringIO import StringIO

from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.models import User

from .lib import create_test_organisation, create_test_ccg, create_test_service, create_test_problem, create_test_trust
from .choices_api import ExampleFileAPITest
from ..models import Organisation

from organisations import auth
from issues.models import Problem


class DevNull(object):
    def write(self, data):
        pass


class CreateNonOrganisationAccountTests(TestCase):

    # The fixture has a bad row that will cause the command to write to stderr -
    # we don't want to see this output during the test run
    def setUp(self):
        self.old_stderr = sys.stderr
        sys.stderr = DevNull()

    def tearDown(self):
        sys.stderr = self.old_stderr

    def _call_command(self, args=[], opts={}):
        call_command('load_users_from_csv', *args, **opts)

    def expect_groups(self, email, expected_groups):
        user = User.objects.get(email=email)
        self.assertTrue(auth.user_in_groups(user, expected_groups))
        other_groups = [group for group in auth.ALL_GROUPS if not group in expected_groups]
        for group in other_groups:
            self.assertFalse(auth.user_in_group(user, group))

    def test_happy_path(self):
        self._call_command([os.path.join(settings.PROJECT_ROOT,
                                         'documentation',
                                         'csv_samples',
                                         'users.csv')])
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


class GetOrganisationRatingsFromChoicesAPITests(ExampleFileAPITest):

    @classmethod
    def setUpClass(cls):
        # Fixture for a particular organisation
        cls._example_file = '41265.xml'
        super(GetOrganisationRatingsFromChoicesAPITests, cls).setUpClass()

    def _call_command(self, *args, **opts):
        call_command('get_organisation_ratings_from_choices_api', *args, **opts)

    def test_happy_path(self):
        # Add an organisation to pull the ratings for
        organisation = create_test_organisation({'organisation_type': 'hospitals',
                                                 'choices_id': 41265})
        self.assertEqual(organisation.average_recommendation_rating, None)

        stdout = StringIO()
        self._call_command(stdout=stdout)
        self.assertEquals(stdout.getvalue(), 'Updated rating for organisation Test Organisation\n')

        organisation = Organisation.objects.get(pk=organisation.id)

        # Because we store things in a float field, there will be some rounding
        # that happens on different systems, but realistically, 3 D.P. is
        # sufficient - I just didn't want to be explicit so that we keep the
        # data they give us as it is.
        self.assertAlmostEqual(organisation.average_recommendation_rating, 4.2857142857142856, places=3)
