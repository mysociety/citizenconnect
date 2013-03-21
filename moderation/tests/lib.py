from django.test import TransactionTestCase

from organisations.models import Organisation
from organisations.tests.lib import create_test_instance, create_test_organisation, AuthorizationTestCase
from issues.models import Problem, Question

class BaseModerationTestCase(AuthorizationTestCase, TransactionTestCase):

    def setUp(self):
        # Add some issues
        super(BaseModerationTestCase, self).setUp()
        self.test_problem = create_test_instance(Problem, {'organisation':self.test_organisation})
        self.test_legal_moderation_problem = create_test_instance(Problem, {'organisation': self.test_organisation,
                                                                            'requires_legal_moderation': True})
        self.test_question = create_test_instance(Question, {})
        self.home_url = '/private/moderate/'
        self.lookup_url = '/private/moderate/lookup'
        self.problem_form_url = '/private/moderate/%d' % self.test_problem.id
        self.confirm_url = '/private/moderate/confirm'
        self.legal_home_url = '/private/moderate/legal'
        self.legal_problem_form_url = '/private/moderate/legal/%d' % self.test_legal_moderation_problem.id
        self.all_case_handler_urls = [self.home_url,
                                     self.lookup_url,
                                     self.problem_form_url,
                                     self.confirm_url]

        self.all_legal_moderator_urls = [self.legal_home_url,
                                         self.legal_problem_form_url]
        self.all_urls = self.all_case_handler_urls + self.all_legal_moderator_urls

    def assert_expected_publication_status(self, expected_status, form_values, url, problem):
        resp = self.client.post(url, form_values)
        problem = Problem.objects.get(pk=problem.id)
        self.assertEqual(problem.publication_status, expected_status)

