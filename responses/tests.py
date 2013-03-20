# Django imports
from django.test import TestCase, TransactionTestCase
from django.core.urlresolvers import reverse

# App imports
from issues.models import Problem, Question
from organisations.tests.lib import create_test_instance, create_test_organisation, AuthorizationTestCase

from .models import ProblemResponse

class ResponseFormTests(AuthorizationTestCase, TransactionTestCase):

    def setUp(self):
        super(ResponseFormTests, self).setUp()
        self.test_problem = create_test_instance(Problem, {'organisation':self.test_organisation})
        self.problem_response_form_url = '/private/response/%s' % self.test_problem.id
        self.login_as(self.provider)

    def test_form_creates_problem_response(self):
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'issue': self.test_problem.id,
            'respond': ''
        }
        resp = self.client.post(self.problem_response_form_url, test_form_values)
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        response = self.test_problem.responses.all()[0]
        self.assertEqual(self.test_problem.responses.count(), 1)
        self.assertEqual(response.response, response_text)

    def test_form_creates_problem_response_and_saves_status(self):
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'issue': self.test_problem.id,
            'issue_status': Problem.RESOLVED,
            'respond': ''
        }
        resp = self.client.post(self.problem_response_form_url, test_form_values)
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        response = self.test_problem.responses.all()[0]
        self.assertEqual(self.test_problem.responses.count(), 1)
        self.assertEqual(response.response, response_text)
        self.assertEqual(self.test_problem.status, Problem.RESOLVED)

    def test_form_allows_empty_response_for_status_change(self):
        response_text = ''
        test_form_values = {
            'response': response_text,
            'issue': self.test_problem.id,
            'issue_status': Problem.RESOLVED,
            'status': ''
        }
        resp = self.client.post(self.problem_response_form_url, test_form_values)
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(self.test_problem.responses.count(), 0)
        self.assertEqual(self.test_problem.status, Problem.RESOLVED)

    def test_form_ignores_response_during_status_change(self):
        response_text = 'I didn\'t mean to respond'
        test_form_values = {
            'response': response_text,
            'issue': self.test_problem.id,
            'issue_status': Problem.RESOLVED,
            'status': ''
        }
        resp = self.client.post(self.problem_response_form_url, test_form_values)
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(self.test_problem.responses.count(), 0)
        self.assertEqual(self.test_problem.status, Problem.RESOLVED)

    def test_form_requires_text_for_responses(self):
        response_text = ''
        test_form_values = {
            'response': response_text,
            'issue': self.test_problem.id,
            'respond': ''
        }
        resp = self.client.post(self.problem_response_form_url, test_form_values)
        self.assertFormError(resp, 'form', 'response', 'This field is required.')

    def test_form_shows_response_confirmation_with_link(self):
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'issue': self.test_problem.id,
            'respond': ''
        }
        resp = self.client.post(self.problem_response_form_url, test_form_values)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "response has been published online")
        self.assertContains(resp, reverse('org-dashboard', kwargs={'ods_code':self.test_organisation.ods_code}))

    def test_form_shows_issue_confirmation_with_link(self):
        response_text = ''
        test_form_values = {
            'response': response_text,
            'issue': self.test_problem.id,
            'issue_status': Problem.RESOLVED,
            'status': ''
        }
        resp = self.client.post(self.problem_response_form_url, test_form_values)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "the Problem status has been updated")
        self.assertContains(resp, reverse('org-dashboard', kwargs={'ods_code':self.test_organisation.ods_code}))

class ResponseFormViewTests(AuthorizationTestCase):

    def setUp(self):
        super(ResponseFormViewTests, self).setUp()
        self.problem = create_test_instance(Problem, {'organisation': self.test_organisation})
        self.response_form_url = '/private/response/%s' % self.problem.id
        self.login_as(self.provider)

    def test_response_page_exists(self):
        resp = self.client.get(self.response_form_url)
        self.assertEqual(resp.status_code, 200)

    def test_response_form_contains_issue_data(self):
        resp = self.client.get(self.response_form_url)
        self.assertContains(resp, self.problem.reference_number)
        self.assertContains(resp, self.problem.issue_type)
        self.assertContains(resp, self.problem.reporter_name)
        self.assertContains(resp, self.problem.description)

    def test_response_form_display_no_responses_message(self):
        resp = self.client.get(self.response_form_url)
        self.assertContains(resp, 'No responses')

    def test_response_form_displays_previous_responses(self):
        # Add some responses
        response1 = ProblemResponse.objects.create(response='response 1', issue=self.problem)
        response2 = ProblemResponse.objects.create(response='response 2', issue=self.problem)
        resp = self.client.get(self.response_form_url)
        self.assertContains(resp, response1.response)
        self.assertContains(resp, response2.response)

    def test_response_form_requires_login(self):
        self.client.logout()
        expected_login_url = "{0}?next={1}".format(reverse('login'), self.response_form_url)
        resp = self.client.get(self.response_form_url)
        self.assertRedirects(resp, expected_login_url)

    def test_other_providers_cant_respond(self):
        self.client.logout()
        self.login_as(self.other_provider)
        resp = self.client.get(self.response_form_url)
        self.assertEqual(resp.status_code, 403)
