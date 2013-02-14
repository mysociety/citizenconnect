from django.test import TestCase

from organisations.models import Organisation
from organisations.tests.lib import create_test_instance, create_test_organisation
from problems.models import Problem
from questions.models import Question

class Viewtests(TestCase):

    def setUp(self):
        self.home_url = '/choices/moderate/'
        self.lookup_url = '/choices/moderate/lookup'
        self.problem_form_url = '/choices/moderate/problem/1'
        self.question_form_url = '/choices/moderate/question/1'
        self.confirm_url = '/choices/moderate/confirm'

    def test_home_view_exists(self):
        resp = self.client.get(self.home_url)
        self.assertEqual(resp.status_code, 200)

    def test_lookup_view_exists(self):
        resp = self.client.get(self.lookup_url)
        self.assertEqual(resp.status_code, 200)

    def test_form_views_exist(self):
        resp = self.client.get(self.problem_form_url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(self.question_form_url)
        self.assertEqual(resp.status_code, 200)

    def test_confirm_view_exists(self):
        resp = self.client.get(self.confirm_url)
        self.assertEqual(resp.status_code, 200)

class HomeViewTests(TestCase):

    def setUp(self):
        self.home_url = '/choices/moderate/'
        # Add some issues
        self.test_organisation = create_test_organisation()
        self.test_problem = create_test_instance(Problem, {'organisation':self.test_organisation})
        self.test_question = create_test_instance(Question, {'organisation':self.test_organisation})

    def test_issues_in_context(self):
        resp = self.client.get(self.home_url)
        self.assertEqual(resp.context['issues'], [self.test_question, self.test_problem])

    def test_issues_displayed(self):
        resp = self.client.get(self.home_url)
        self.assertContains(resp, self.test_problem.summary)
        self.assertContains(resp, self.test_question.summary)

    def test_issues_link_to_moderate_form(self):
        expected_problem_url = 'choices/moderate/problem/%d' % self.test_problem.id
        expected_question_url = 'choices/moderate/question/%d' % self.test_question.id

        resp = self.client.get(self.home_url)
        self.assertContains(resp, expected_problem_url)
        self.assertContains(resp, expected_question_url)

