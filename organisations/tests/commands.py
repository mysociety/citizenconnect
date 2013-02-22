from django.test import TestCase
from django.core import mail
from django.core.management import call_command

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
