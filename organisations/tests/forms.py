# Django imports
from django.test import TestCase

# App imports
from problems.models import Problem

from . import create_test_instance

class ResponseFormTests(TestCase):

    def setUp(self):
        self.problem = create_test_instance(Problem, {})
        self.response_form_url = '/private/response/problem/%s' % self.problem.id

    def test_response_form_doesnt_update_message(self):
        updated_description = "{0} updated", format(self.problem.description)
        test_form_values = {
            'status': self.problem.status,
            'description': updated_description
        }
        resp = self.client.post(self.response_form_url)
        problem = Problem.objects.get(pk=self.problem.id)
        self.assertNotEqual(problem.description, updated_description)

    def test_form_sets_response(self):
        response = 'This problem is solved'
        test_form_values = {
            'status': self.problem.status,
            'response': response
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        problem = Problem.objects.get(pk=self.problem.id)
        self.assertEqual(problem.response, response)

    def test_form_sets_status(self):
        status = Problem.RESOLVED
        test_form_values = {
            'status': status
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        problem = Problem.objects.get(pk=self.problem.id)
        self.assertEqual(problem.status, status)