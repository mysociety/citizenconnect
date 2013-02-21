from django.test import TransactionTestCase

from organisations.models import Organisation
from organisations.tests.lib import create_test_instance, create_test_organisation
from issues.models import Problem, Question

class BaseModerationTestCase(TransactionTestCase):

    def setUp(self):
        # Add some issues
        self.test_organisation = create_test_organisation()
        self.test_problem = create_test_instance(Problem, {'organisation':self.test_organisation})
        self.test_question = create_test_instance(Question, {'organisation':self.test_organisation})
        self.home_url = '/private/moderate/'
        self.lookup_url = '/private/moderate/lookup'
        self.problem_form_url = '/private/moderate/problem/%d' % self.test_problem.id
        self.question_form_url = '/private/moderate/question/%d' % self.test_question.id
        self.confirm_url = '/private/moderate/confirm'