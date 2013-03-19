from django.core.urlresolvers import reverse

from organisations.models import Organisation
from organisations.tests.lib import create_test_instance, create_test_organisation
from issues.models import Problem, Question

from .lib import BaseModerationTestCase

class LookupFormTests(BaseModerationTestCase):

    def setUp(self):
        super(LookupFormTests, self).setUp()
        self.closed_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                             'status': Problem.RESOLVED})
        self.moderated_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                                'moderated': Problem.MODERATED})
        self.login_as(self.case_handler)

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
        self.assertFormError(resp, 'form', None, 'Sorry, there are no unmoderated problems with that reference number')

    def test_form_rejects_questions(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Question.PREFIX, self.test_question.id)})
        self.assertFormError(resp, 'form', None, 'Sorry, that reference number is not recognised')

    def test_form_rejects_moderated_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.moderated_problem.id)})
        self.assertFormError(resp, 'form', None, 'Sorry, there are no unmoderated problems with that reference number')

    def test_form_allows_closed_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.closed_problem.id)})
        self.assertRedirects(resp, '/private/moderate/{0}'.format(self.closed_problem.id))

class ModerationFormTests(BaseModerationTestCase):

    def setUp(self):
        super(ModerationFormTests, self).setUp()
        self.login_as(self.case_handler)

    def test_moderation_form_sets_moderated(self):
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'publish': ''
        }
        resp = self.client.post(self.problem_form_url, test_form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.moderated, Problem.MODERATED)

    def test_moderation_form_updates_message(self):
        updated_description = "{0} updated".format(self.test_problem.description)
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'description': updated_description,
            'moderated': self.test_problem.moderated,
            'publish': ''
        }
        resp = self.client.post(self.problem_form_url, test_form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.description, updated_description)

    def test_form_sets_publication_status_to_published(self):
        expected_status = Problem.PUBLISHED
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'publish': ''
        }
        resp = self.client.post(self.problem_form_url, test_form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.publication_status, expected_status)

    def test_form_sets_publication_status_to_private(self):
        expected_status = Problem.HIDDEN
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'keep_private': ''
        }
        resp = self.client.post(self.problem_form_url, test_form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.publication_status, expected_status)

    def test_form_redirects_to_confirm_url(self):
        status = Problem.RESOLVED
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'keep_private': ''
        }
        resp = self.client.post(self.problem_form_url, test_form_values)
        self.assertRedirects(resp, reverse('moderate-confirm'))
