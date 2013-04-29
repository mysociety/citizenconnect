import logging
from mock import patch
import os
import sys

from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User

from .lib import create_test_organisation, create_test_ccg, create_test_service, create_test_problem

from organisations import auth
from issues.models import Problem


class DevNull(object):
    def write(self, data):
        pass


class EmailProblemsToProviderTests(TestCase):

    def setUp(self):
        # Add some test data
        self.test_organisation = create_test_organisation({"email": "recipient@example.com"})
        self.test_service = create_test_service({'organisation': self.test_organisation})
        self.test_problem = create_test_problem({'organisation': self.test_organisation,
                                                 'service': self.test_service,
                                                 'reporter_name': 'Problem reporter',
                                                 'reporter_email': 'problem@example.com',
                                                 'reporter_phone': '123456789'})

        self.other_test_problem = create_test_problem({'organisation': self.test_organisation,
                                                       'service': self.test_service,
                                                       'reporter_name': 'Problem reporter',
                                                       'reporter_email': 'problem@example.com',
                                                       'reporter_phone': '123456789'})

    def _call_command(self):
        args = []
        opts = {}
        call_command('email_issues_to_providers', *args, **opts)

    def test_happy_path(self):
        self._call_command()

        # intro mail, problem mail, other problem mail
        self.assertEqual(len(mail.outbox), 3)

        first_mail = mail.outbox[1]
        self.assertEqual(first_mail.subject, 'Care Connect: New Problem')
        self.assertEqual(first_mail.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(first_mail.to, ['recipient@example.com'])
        self.assertTrue(self.test_problem.reporter_name in first_mail.body)
        self.assertTrue(self.test_problem.reporter_email in first_mail.body)
        self.assertTrue(self.test_problem.category in first_mail.body)
        self.assertTrue(self.test_problem.description in first_mail.body)
        dashboard_url = settings.SITE_BASE_URL + reverse('org-dashboard',
                                                         kwargs={'ods_code': self.test_problem.organisation.ods_code})
        self.assertTrue(dashboard_url in first_mail.body)

        # Check that problems were marked as mailed
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertTrue(self.test_problem.mailed)
        self.other_test_problem = Problem.objects.get(pk=self.other_test_problem.id)
        self.assertTrue(self.other_test_problem.mailed)

    def test_sends_no_emails_when_none_to_send(self):
        self.test_problem.mailed = True
        self.test_problem.save()

        self.other_test_problem.mailed = True
        self.other_test_problem.save()

        self._call_command()

        self.assertEqual(len(mail.outbox), 0)

    def test_displays_correct_contact_method(self):

        # Just use one problem for this test
        self.other_test_problem.mailed = True
        self.other_test_problem.save()

        self.test_problem.preferred_contact_method = Problem.CONTACT_PHONE
        self.test_problem.reporter_phone = '1234567'
        self.test_problem.save()
        self._call_command()

        first_mail = mail.outbox[1]

        self.assertTrue(self.test_problem.reporter_phone in first_mail.body)
        self.assertTrue(self.test_problem.reporter_email not in first_mail.body)

    def test_handles_errors_in_sending_mails(self):
        # Quiet logging for this test
        logging.disable(logging.CRITICAL)
        # Make send_mail throw an exception for the first call
        with patch.object(mail, 'send_mail') as mock_send_mail:

            # intro mail, intro mail again, other problem mail
            mock_send_mail.side_effect = [Exception('A fake error in sending mail'), 1, 1]
            self._call_command()
            # Check it still sent one mail
            self.assertEqual(mock_send_mail.call_count, 3)
            # Check that the errored issue is still marked as not mailed
            self.test_problem = Problem.objects.get(pk=self.test_problem.id)
            self.assertFalse(self.test_problem.mailed)
            # # And that the successful one got marked as mailed
            self.other_test_problem = Problem.objects.get(pk=self.other_test_problem.id)
            self.assertTrue(self.other_test_problem.mailed)

        logging.disable(logging.NOTSET)


class CreateAccountsForOrganisationsAndCCGsTests(TestCase):

    def _call_command(self):
        args = []
        opts = {}
        call_command('create_accounts_for_organisations_and_ccgs', *args, **opts)

    def test_happy_path(self):
        # Quiet logging for this test - there a CCGs loaded that don't have email
        logging.disable(logging.CRITICAL)

        test_organisation_with_email = create_test_organisation({"email": "org@example.com"})
        test_ccg_with_email = create_test_ccg({"email": "ccg@example.com"})

        self._call_command()

        # Check that user was created
        for obj in [test_organisation_with_email, test_ccg_with_email]:
            users = obj.__class__.objects.get(pk=obj.id).users
            self.assertEqual(users.count(), 1)
            self.assertEqual(users.all()[0].email, obj.email)

        logging.disable(logging.NOTSET)

    def test_handles_orgs_with_no_email(self):  # ISSUE-329
        # Quiet logging for this test
        logging.disable(logging.CRITICAL)

        test_organisation_no_email = create_test_organisation({"email": ""})
        test_ccg_no_email = create_test_ccg({"email": ""})

        # This would raise an error if it didn't handle it
        self._call_command()

        # Check that user was created
        for obj in [test_organisation_no_email, test_ccg_no_email]:
            users = obj.__class__.objects.get(pk=obj.id).users
            self.assertEqual(users.count(), 0)

        logging.disable(logging.NOTSET)


class CreateNonOrganisationAccountTests(TestCase):

    # The fixture has a bad row that will cause the command to write to stderr -
    # we don't want to see this output during the test run
    def setUp(self):
        self.old_stderr = sys.stderr
        sys.stderr = DevNull()

    def tearDown(self):
        sys.stderr = self.old_stderr

    def _call_command(self, args=[], opts={}):
        call_command('create_non_organisation_accounts', *args, **opts)

    def expect_groups(self, email, expected_groups):
        user = User.objects.get(email=email)
        self.assertTrue(auth.user_in_groups(user, expected_groups))
        other_groups = [group for group in auth.ALL_GROUPS if not group in expected_groups]
        for group in other_groups:
            self.assertFalse(auth.user_in_group(user, group))

    def test_happy_path(self):
        self._call_command([os.path.join(settings.PROJECT_ROOT,
                                         'organisations',
                                         'fixtures',
                                         'example_accounts.csv')])
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
