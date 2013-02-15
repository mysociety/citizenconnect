from django.test import TransactionTestCase

from organisations.models import Organisation
from organisations.tests.lib import create_test_instance, create_test_organisation
from problems.models import Problem
from questions.models import Question

from .lib import BaseModerationTestCase

class LookupFormTests(BaseModerationTestCase):

    def setUp(self):
        super(LookupFormTests, self).setUp()
        self.closed_problem = create_test_instance(Problem, {'organisation':self.test_organisation, 'status': Problem.RESOLVED})
        self.closed_problem2 = create_test_instance(Problem, {'organisation':self.test_organisation, 'status': Problem.NOT_RESOLVED})
        self.closed_question = create_test_instance(Question, {'organisation':self.test_organisation, 'status': Question.RESOLVED})

    def test_happy_path(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.test_problem.id)})
        self.assertRedirects(resp, self.problem_form_url)

    def test_form_rejects_empty_submissions(self):
        resp = self.client.post(self.lookup_url, {})
        self.assertFormError(resp, 'form', 'reference_number', 'This field is required.')

    def test_form_rejects_unknown_prefixes(self):
        resp = self.client.post(self.lookup_url, {'reference_number': 'a123'})
        self.assertFormError(resp, 'form', None, 'Sorry, that reference number is not recognised')

    def test_form_rejects_unknown_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}12300'.format(Problem.PREFIX)})
        self.assertFormError(resp, 'form', None, 'Sorry, there are no open problems or questions with that reference number')

    def test_form_rejects_unknown_questions(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}12300'.format(Question.PREFIX)})
        self.assertFormError(resp, 'form', None, 'Sorry, there are no open problems or questions with that reference number')

    def test_form_rejects_closed_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.closed_problem.id)})
        self.assertFormError(resp, 'form', None, 'Sorry, there are no open problems or questions with that reference number')

        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.closed_problem2.id)})
        self.assertFormError(resp, 'form', None, 'Sorry, there are no open problems or questions with that reference number')

    def test_form_rejects_closed_questions(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Question.PREFIX, self.closed_question.id)})
        self.assertFormError(resp, 'form', None, 'Sorry, there are no open problems or questions with that reference number')
