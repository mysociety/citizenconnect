from django.core.urlresolvers import reverse

from organisations.models import Organisation
from organisations.tests.lib import create_test_instance, create_test_organisation
from issues.models import Problem, Question

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

class ModerationFormTests(BaseModerationTestCase):

    def setUp(self):
        self.problem = create_test_instance(Problem, {})
        self.moderation_form_url = '/private/moderate/problem/%s' % self.problem.id

    def test_moderation_form_doesnt_update_message(self):
        updated_description = "{0} updated".format(self.problem.description)
        test_form_values = {
            'status': self.problem.status,
            'description': updated_description
        }
        resp = self.client.post(self.moderation_form_url)
        problem = Problem.objects.get(pk=self.problem.id)
        self.assertNotEqual(problem.description, updated_description)

    def test_form_sets_status(self):
        status = Problem.RESOLVED
        test_form_values = {
            'status': status
        }
        resp = self.client.post(self.moderation_form_url, test_form_values)
        problem = Problem.objects.get(pk=self.problem.id)
        self.assertEqual(problem.status, status)

    def test_form_redirects_to_confirm_url(self):
        status = Problem.RESOLVED
        test_form_values = {
            'status': status
        }
        resp = self.client.post(self.moderation_form_url, test_form_values)
        self.assertRedirects(resp, reverse('moderate-confirm'))
