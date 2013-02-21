# Django imports
from django.test import TestCase

# App imports
from problems.models import Problem
from questions.models import Question
from organisations.tests.lib import create_test_instance, create_test_organisation

from .models import ProblemResponse, QuestionResponse

class ResponseFormTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation()
        self.test_problem = create_test_instance(Problem, {'organisation':self.test_organisation})
        self.test_question = create_test_instance(Question, {'organisation':self.test_organisation})
        self.problem_response_form_url = '/private/response/problem/%s' % self.test_problem.id
        self.question_response_form_url = '/private/response/question/%s' % self.test_problem.id

    def test_form_creates_problem_response(self):
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'message': self.test_problem.id
        }
        resp = self.client.post(self.problem_response_form_url, test_form_values)
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        response = self.test_problem.responses.all()[0]
        self.assertEqual(self.test_problem.responses.count(), 1)
        self.assertEqual(response.response, response_text)

    def test_form_creates_question_response(self):
        response_text = 'This question is solved'
        test_form_values = {
            'response': response_text,
            'message': self.test_question.id
        }
        resp = self.client.post(self.question_response_form_url, test_form_values)
        self.test_question = Question.objects.get(pk=self.test_question.id)
        response = self.test_question.responses.all()[0]
        self.assertEqual(self.test_question.responses.count(), 1)
        self.assertEqual(response.response, response_text)

    def test_form_saves_problem_status(self):
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'message': self.test_problem.id,
            'message_status': Problem.RESOLVED
        }
        resp = self.client.post(self.problem_response_form_url, test_form_values)
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(self.test_problem.status, Problem.RESOLVED)

    def test_form_saves_question_status(self):
        response_text = 'This question is solved'
        test_form_values = {
            'response': response_text,
            'message': self.test_question.id,
            'message_status': Question.RESOLVED
        }
        resp = self.client.post(self.question_response_form_url, test_form_values)
        self.test_question = Question.objects.get(pk=self.test_question.id)
        self.assertEqual(self.test_question.status, Question.RESOLVED)

class ResponseFormViewTests(TestCase):

    def setUp(self):
        self.problem = create_test_instance(Problem, {})
        self.response_form_url = '/private/response/problem/%s' % self.problem.id

    def test_response_page_exists(self):
        resp = self.client.get(self.response_form_url)
        self.assertEqual(resp.status_code, 200)

    def test_response_form_contains_message_data(self):
        resp = self.client.get(self.response_form_url)
        self.assertContains(resp, self.problem.reference_number)
        self.assertContains(resp, self.problem.issue_type)
        self.assertContains(resp, self.problem.reporter_name)
        self.assertContains(resp, self.problem.reporter_phone)
        self.assertContains(resp, self.problem.reporter_email)
        self.assertContains(resp, self.problem.description)

    def test_response_form_display_no_responses_message(self):
        resp = self.client.get(self.response_form_url)
        self.assertContains(resp, 'No responses')

    def test_response_form_displays_previous_responses(self):
        # Add some responses
        response1 = ProblemResponse.objects.create(response='response 1', message=self.problem)
        response2 = ProblemResponse.objects.create(response='response 2', message=self.problem)
        resp = self.client.get(self.response_form_url)
        self.assertContains(resp, response1.response)
        self.assertContains(resp, response2.response)

class ResponseConfirmTests(TestCase):

    def setUp(self):
        self.response_confirm_url = '/private/response/confirm'

    def test_response_page_exists(self):
        resp = self.client.get(self.response_confirm_url)
        self.assertEqual(resp.status_code, 200)