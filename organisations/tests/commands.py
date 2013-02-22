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

    def test_happy_path(self):
        args = []
        opts = {}
        call_command('email_issues_to_providers', *args, **opts)
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
