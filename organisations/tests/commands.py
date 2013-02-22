from mock import patch

from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.conf import settings

from .lib import create_test_organisation, create_test_service, create_test_instance

from issues.models import Question, Problem

class EmailIssuesToProviderTests(TestCase):

    def setUp(self):
        # Add some test data
        self.test_organisation = create_test_organisation()
        self.test_service = create_test_service({'organisation': self.test_organisation})
        self.test_problem = create_test_instance(Problem, {'organisation': self.test_organisation, 'service': self.test_service})
        self.test_question = create_test_instance(Question, {'organisation': self.test_organisation, 'service': self.test_service})

    def _call_command(self):
        args = []
        opts = {}
        call_command('email_issues_to_providers', *args, **opts)

    def test_happy_path(self):
        self._call_command()

        self.assertEqual(len(mail.outbox), 2)

        first_mail = mail.outbox[0]
        self.assertEqual(first_mail.subject, 'Care Connect: New Problem')
        self.assertEqual(first_mail.from_email, 'no-reply@citizenconnect.mysociety.org')
        self.assertEqual(first_mail.to, ['steve@mysociety.org'])
        self.assertTrue(self.test_problem.reporter_name in first_mail.body)
        self.assertTrue(self.test_problem.reporter_email in first_mail.body)
        self.assertTrue(self.test_problem.category in first_mail.body)
        self.assertTrue(self.test_problem.description in first_mail.body)
        dashboard_url = settings.SITE_BASE_URL + reverse('org-dashboard', kwargs={'ods_code':self.test_problem.organisation.ods_code})
        self.assertTrue(dashboard_url in first_mail.body)

        second_mail = mail.outbox[1]
        self.assertEqual(second_mail.subject, 'Care Connect: New Question')
        self.assertEqual(second_mail.from_email, 'no-reply@citizenconnect.mysociety.org')
        self.assertEqual(second_mail.to, ['steve@mysociety.org'])
        self.assertTrue(self.test_question.reporter_name in second_mail.body)
        self.assertTrue(self.test_question.reporter_email in second_mail.body)
        self.assertTrue(self.test_question.category in second_mail.body)
        self.assertTrue(self.test_question.description in second_mail.body)
        dashboard_url = settings.SITE_BASE_URL + reverse('org-dashboard', kwargs={'ods_code':self.test_question.organisation.ods_code})
        self.assertTrue(dashboard_url in second_mail.body)

        # Check that messages were marked as mailed
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertTrue(self.test_problem.mailed)
        self.test_question = Question.objects.get(pk=self.test_question.id)
        self.assertTrue(self.test_question.mailed)

    def test_sends_no_emails_when_none_to_send(self):
        self.test_problem.mailed = True
        self.test_problem.save()
        self.test_question.mailed = True
        self.test_question.save()

        self._call_command()

        self.assertEqual(len(mail.outbox), 0)

    def test_displays_correct_contact_method(self):
        self.test_problem.preferred_contact_method = Problem.CONTACT_PHONE
        self.test_problem.reporter_phone = '1234567'
        self.test_problem.save()

        self.test_question.reporter_phone = '9101112'

        self._call_command()

        first_mail = mail.outbox[0]
        self.assertTrue(self.test_problem.reporter_phone in first_mail.body)
        self.assertTrue(self.test_problem.reporter_email not in first_mail.body)

        second_mail = mail.outbox[1]
        self.assertTrue(self.test_question.reporter_phone not in second_mail.body)
        self.assertTrue(self.test_question.reporter_email in second_mail.body)

    def test_handles_errors_in_sending_mails(self):
        # Make send_mail throw an exception for the first call
        old_send_mail = mail.send_mail
        with patch.object(mail, 'send_mail') as mock_send_mail:
            mock_send_mail.side_effect = [Exception('A fake error in sending mail'), 1]
            self._call_command()
            # Check it still sent one mail
            self.assertEqual(mock_send_mail.call_count, 2)
            # Check that the errored message is still marked as not mailed
            self.test_problem = Problem.objects.get(pk=self.test_problem.id)
            self.assertFalse(self.test_problem.mailed)
            # And that the successful one got marked as mailed
            self.test_question = Question.objects.get(pk=self.test_question.id)
            self.assertTrue(self.test_question.mailed)


