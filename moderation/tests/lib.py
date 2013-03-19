from django.test import TransactionTestCase

from organisations.models import Organisation
from organisations.tests.lib import create_test_instance, create_test_organisation, AuthorizationTestCase
from issues.models import Problem, Question

class BaseModerationTestCase(AuthorizationTestCase, TransactionTestCase):

    def setUp(self):
        # Add some issues
        super(BaseModerationTestCase, self).setUp()
        self.test_problem = create_test_instance(Problem, {'organisation':self.test_organisation})
        self.test_question = create_test_instance(Question, {})
        self.home_url = '/private/moderate/'
        self.lookup_url = '/private/moderate/lookup'
        self.problem_form_url = '/private/moderate/%d' % self.test_problem.id
        self.confirm_url = '/private/moderate/confirm'
        self.all_urls = [self.home_url, self.lookup_url, self.problem_form_url, self.confirm_url]