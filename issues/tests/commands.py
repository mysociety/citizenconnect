import logging
from mock import patch
from datetime import datetime, timedelta

from django.test import TestCase
from django.core.management import call_command
from django.core import mail
from django.core.urlresolvers import reverse
from django.utils.timezone import utc
from django.conf import settings
from django.test.utils import override_settings

from organisations.tests.lib import (create_test_organisation_parent,
                                     create_test_organisation,
                                     create_test_service,
                                     create_test_problem)
from ..models import Problem


class EmailToReportersBase(object):

    def setUp(self):
        self.test_organisation = create_test_organisation({'name': 'Fab Organisation'})
        self.test_service = create_test_service({'organisation': self.test_organisation})
        self.test_problem = create_test_problem({'organisation': self.test_organisation,
                                                 'service': self.test_service,
                                                 'cobrand': 'choices',
                                                 'reporter_name': 'Problem reporter',
                                                 'reporter_email': 'problem@example.com',
                                                 'reporter_phone': '123456789',
                                                 'confirmation_required': True})


class EmailConfirmationsToReportersTests(EmailToReportersBase, TestCase):

    def _call_command(self):
        args = []
        opts = {}
        call_command('email_confirmations_to_reporters', *args, **opts)

    @override_settings(SURVEY_INTERVAL_IN_DAYS=99)
    def test_happy_path(self):
        self._call_command()
        self.assertEqual(len(mail.outbox), 1)
        first_mail = mail.outbox[0]
        self.assertEqual(first_mail.subject, 'Thank you for reporting your problem.')
        self.assertEqual(first_mail.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(first_mail.to, ['problem@example.com'])
        self.assertTrue("Dear %s," % self.test_problem.reporter_name in first_mail.body)
        self.assertTrue("Thank you for reporting your problem." in first_mail.body)
        self.assertTrue('Fab Organisation' in first_mail.body)
        self.assertTrue('{0} days after posting'.format(settings.SURVEY_INTERVAL_IN_DAYS) in first_mail.body)

        self.assertTrue(Problem.objects.get(pk=self.test_problem.id).confirmation_sent)

    def test_sends_no_emails_when_none_to_send(self):
        self.test_problem.confirmation_sent = datetime.utcnow().replace(tzinfo=utc)
        self.test_problem.save()
        self._call_command()
        self.assertEqual(len(mail.outbox), 0)

    def test_sends_no_emails_when_none_required(self):
        self.test_problem.confirmation_required = False
        self.test_problem.save()
        self._call_command()
        self.assertEqual(len(mail.outbox), 0)


class EmailSurveysToReportersTests(EmailToReportersBase, TestCase):

    def setUp(self):
        super(EmailSurveysToReportersTests, self).setUp()
        self.set_problem_age()

    def set_problem_age(self):
        now = datetime.utcnow().replace(tzinfo=utc)
        self.test_problem_age = settings.SURVEY_INTERVAL_IN_DAYS+1
        interval = timedelta(days=self.test_problem_age)
        Problem.objects.filter(pk=self.test_problem.id).update(created=now-interval)

    def _call_command(self):
        args = []
        opts = {}
        call_command('email_surveys_to_reporters', *args, **opts)

    def test_happy_path(self):
        self._call_command()
        self.assertEqual(len(mail.outbox), 1)
        first_mail = mail.outbox[0]
        self.assertEqual(first_mail.subject, 'Care Connect Survey')
        self.assertEqual(first_mail.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(first_mail.to, ['problem@example.com'])
        self.assertTrue("Dear %s," % self.test_problem.reporter_name in first_mail.body)
        self.assertTrue("Recently you reported a problem" in first_mail.body)
        self.assertTrue('Fab Organisation' in first_mail.body)
        self.assertTrue('/choices/' in first_mail.body)

        self.assertTrue(Problem.objects.get(pk=self.test_problem.id).survey_sent)

    def test_sends_no_emails_when_none_to_send(self):
        self.test_problem.survey_sent = datetime.utcnow().replace(tzinfo=utc)
        self.test_problem.save()
        self._call_command()
        self.assertEqual(len(mail.outbox), 0)

    def test_sends_links_using_correct_cobrand(self):
        self.test_problem.cobrand = 'myhealthlondon'
        self.test_problem.save()
        self.set_problem_age()
        self._call_command()
        self.assertEqual(len(mail.outbox), 1)
        first_mail = mail.outbox[0]
        self.assertTrue('/myhealthlondon/' in first_mail.body)

    def test_does_not_send_survey_for_a_problem_in_a_hidden_state(self):
        self.test_problem.status = Problem.ABUSIVE
        self.test_problem.save()
        self.set_problem_age()
        self._call_command()
        self.assertEqual(len(mail.outbox), 0)


class EmailProblemsToOrganisationParentTests(TestCase):

    def setUp(self):
        # Add some test data
        self.test_trust = create_test_organisation_parent({
            "email": "recipient@example.com",
            "secondary_email": "recipient2@example.com",
        })
        self.test_organisation = create_test_organisation({"parent": self.test_trust})

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

        # problem mail, other problem mail
        self.assertEqual(len(mail.outbox), 2)

        first_mail = mail.outbox[0]
        self.assertEqual(first_mail.subject, 'Care Connect: New Problem')
        self.assertEqual(first_mail.from_email, settings.DEFAULT_FROM_EMAIL)
        expected_recipients = [
            self.test_trust.email,
            self.test_trust.secondary_email
        ]
        self.assertEqual(first_mail.to, expected_recipients)
        self.assertTrue(self.test_problem.reporter_name in first_mail.body)
        self.assertTrue(self.test_problem.reporter_email in first_mail.body)
        self.assertTrue(self.test_problem.category in first_mail.body)
        self.assertTrue(self.test_problem.description in first_mail.body)
        dashboard_url = settings.SITE_BASE_URL + reverse('org-parent-dashboard',
                                                         kwargs={'code': self.test_problem.organisation.parent.code})
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

        first_mail = mail.outbox[0]

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
            # Check it tried to send two emails
            self.assertEqual(mock_send_mail.call_count, 2)
            # Check that the errored issue is still marked as not mailed
            self.test_problem = Problem.objects.get(pk=self.test_problem.id)
            self.assertFalse(self.test_problem.mailed)
            # # And that the successful one got marked as mailed
            self.other_test_problem = Problem.objects.get(pk=self.other_test_problem.id)
            self.assertTrue(self.other_test_problem.mailed)

        logging.disable(logging.NOTSET)

