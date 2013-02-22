from django.test import TestCase

from organisations.tests import create_test_instance, create_test_organisation
from responses.models import QuestionResponse, ProblemResponse

from ..models import Question, Problem

class QuestionPublicViewTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation()
        self.test_question = create_test_instance(Question, {'organisation': self.test_organisation})

    def test_public_question_page_exists(self):
        resp = self.client.get("/choices/question/{0}".format(self.test_question.id))
        self.assertEqual(resp.status_code, 200)

    def test_public_question_displays_organisation_name(self):
        resp = self.client.get("/choices/question/{0}".format(self.test_question.id))
        self.assertContains(resp, self.test_organisation.name, count=1, status_code=200)

    def test_public_question_displays_responses(self):
        response1 = QuestionResponse.objects.create(response="response 1", message=self.test_question)
        response2 = QuestionResponse.objects.create(response="response 2", message=self.test_question)
        resp = self.client.get("/choices/question/{0}".format(self.test_question.id))
        self.assertContains(resp, response1.response, count=1, status_code=200)
        self.assertContains(resp, response2.response, count=1, status_code=200)

    def test_public_question_displays_empty_response_message(self):
        resp = self.client.get("/choices/question/{0}".format(self.test_question.id))
        self.assertContains(resp, "No responses", count=1, status_code=200)

class QuestionProviderPickerTests(TestCase):

    def setUp(self):
        super(QuestionProviderPickerTests, self).setUp()
        self.results_url = "/choices/question/pick-provider?organisation_type=gppractices&location=London"

    def test_results_page_exists(self):
        resp = self.client.get(self.results_url)
        self.assertEqual(resp.status_code, 200)

class ProblemPublicViewTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation()
        self.test_problem = create_test_instance(Problem, {'organisation': self.test_organisation})

    def test_public_problem_page_exists(self):
        resp = self.client.get("/choices/problem/{0}".format(self.test_problem.id))
        self.assertEqual(resp.status_code, 200)

    def test_public_problem_displays_organisation_name(self):
        resp = self.client.get("/choices/problem/{0}".format(self.test_problem.id))
        self.assertContains(resp, self.test_organisation.name, count=1, status_code=200)

    def test_public_problem_displays_responses(self):
        response1 = ProblemResponse.objects.create(response="response 1", message=self.test_problem)
        response2 = ProblemResponse.objects.create(response="response 2", message=self.test_problem)
        resp = self.client.get("/choices/problem/{0}".format(self.test_problem.id))
        self.assertContains(resp, response1.response, count=1, status_code=200)
        self.assertContains(resp, response2.response, count=1, status_code=200)

    def test_public_problem_displays_empty_response_message(self):
        resp = self.client.get("/choices/problem/{0}".format(self.test_problem.id))
        self.assertContains(resp, "No responses", count=1, status_code=200)

class ProblemProviderPickerTests(TestCase):

    def setUp(self):
        self.results_url = "/choices/problem/pick-provider?organisation_type=gppractices&location=London"

    def test_results_page_exists(self):
        resp = self.client.get(self.results_url)
        self.assertEqual(resp.status_code, 200)

