from django.test import TransactionTestCase

from organisations.models import Organisation
from organisations.tests.lib import create_test_instance, create_test_organisation
from problems.models import Problem
from questions.models import Question

class BaseModerateViewTestCase(TransactionTestCase):

    def setUp(self):
        # Add some issues
        self.test_organisation = create_test_organisation()
        self.test_problem = create_test_instance(Problem, {'organisation':self.test_organisation})
        self.test_question = create_test_instance(Question, {'organisation':self.test_organisation})
        self.home_url = '/choices/moderate/'
        self.lookup_url = '/choices/moderate/lookup'
        self.problem_form_url = '/choices/moderate/problem/%d' % self.test_problem.id
        self.question_form_url = '/choices/moderate/question/%d' % self.test_question.id
        self.confirm_url = '/choices/moderate/confirm'

class BasicViewTests(BaseModerateViewTestCase):

    def setUp(self):
        super(BasicViewTests, self).setUp()

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

class HomeViewTests(BaseModerateViewTestCase):

    def setUp(self):
        super(HomeViewTests, self).setUp()
        self.closed_problem = create_test_instance(Problem, {'organisation':self.test_organisation, 'status': Problem.RESOLVED})
        self.closed_problem2 = create_test_instance(Problem, {'organisation':self.test_organisation, 'status': Problem.NOT_RESOLVED})
        self.closed_question = create_test_instance(Question, {'organisation':self.test_organisation, 'status': Question.RESOLVED})

    def test_issues_in_context(self):
        resp = self.client.get(self.home_url)
        self.assertEqual(resp.context['issues'], [self.test_question, self.test_problem])

    def test_closed_issues_not_in_context(self):
        resp = self.client.get(self.home_url)
        self.assertTrue(self.closed_problem not in resp.context['issues'])
        self.assertTrue(self.closed_problem2 not in resp.context['issues'])
        self.assertTrue(self.closed_question not in resp.context['issues'])

    def test_issues_displayed(self):
        resp = self.client.get(self.home_url)
        self.assertContains(resp, self.test_problem.summary)
        self.assertContains(resp, self.test_question.summary)

    def test_issues_link_to_moderate_form(self):
        resp = self.client.get(self.home_url)
        self.assertContains(resp, self.problem_form_url)
        self.assertContains(resp, self.question_form_url)

class ModerateFormViewTests(BaseModerateViewTestCase):

    def setUp(self):
        super(ModerateFormViewTests, self).setUp()

    def test_problem_in_context(self):
        resp = self.client.get(self.problem_form_url)
        self.assertEqual(resp.context['message'], self.test_problem)

    def test_question_in_context(self):
        resp = self.client.get(self.question_form_url)
        self.assertEqual(resp.context['message'], self.test_question)

    def test_message_data_displayed(self):
        resp = self.client.get(self.problem_form_url)
        self.assertContains(resp, self.test_problem.id)
        self.assertContains(resp, self.test_problem.reporter_name)
        self.assertContains(resp, self.test_problem.description)
        self.assertContains(resp, self.test_problem.organisation)

class LookupViewTests(BaseModerateViewTestCase):

    def setUp(self):
        super(LookupViewTests, self).setUp()

    def test_problem_in_context(self):
        resp = self.client.get(self.problem_form_url)
        self.assertEqual(resp.context['message'], self.test_problem)
