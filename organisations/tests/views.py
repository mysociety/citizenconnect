import os

# Django imports
from django.test import TestCase

# App imports
import organisations
from . import MockedChoicesAPITest
from . import create_test_instance
from problems.models import Problem
from questions.models import Question

class OrganisationSummaryTests(MockedChoicesAPITest):

    def setUp(self):
        super(OrganisationSummaryTests, self).setUp()
        atts = {'organisation_type': 'gppractices',
                'choices_id' : 12702}
        atts.update({'category': 'cleanliness'})
        self.cleanliness_problem = create_test_instance(Problem, atts)
        atts.update({'category': 'staff'})
        self.staff_problem = create_test_instance(Problem, atts)
        atts.update({'category': 'services'})
        self.services_question = create_test_instance(Question, atts)
        atts.update({'category': 'general'})
        self.general_question = create_test_instance(Question, atts)
        self.public_summary_url = '/choices/stats/summary/gppractices/12702'
        self.private_summary_url = '/private/summary/gppractices/12702'
        self.urls = [self.public_summary_url, self.private_summary_url]

    def test_summary_page_exists(self):
        for url in self.urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_summary_page_shows_organisation_name(self):
        for url in self.urls:
            resp = self.client.get(url)
            self.assertTrue('Test Organisation Name Outcomes' in resp.content)

    def test_summary_page_has_problems(self):
        for url in self.urls:
            resp = self.client.get(url)
            self.assertEqual(len(resp.context['problems']), 2)
            self.assertEqual(resp.context['problems'][0].id, self.staff_problem.id)
            self.assertEqual(resp.context['problems'][1].id, self.cleanliness_problem.id)
            self.assertEqual(resp.context['problems_total'], {'week': 2, 'four_weeks': 2, 'six_months': 2})
            expected_status_counts = [{'week': 2,
                                       'four_weeks': 2,
                                       'six_months': 2,
                                       'description': 'Received but not acknowledged'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'description': 'Acknowledged but not addressed'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'description': 'Addressed - problem solved'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'description': 'Addressed - unable to solve'}]
            self.assertEqual(resp.context['problems_by_status'], expected_status_counts)

    def test_summary_page_has_questions(self):
        for url in self.urls:
            resp = self.client.get(url)
            self.assertEqual(len(resp.context['questions']), 2)
            self.assertEqual(resp.context['questions'][0].id, self.general_question.id)
            self.assertEqual(resp.context['questions'][1].id, self.services_question.id)
            expected_status_counts = [{'week': 2,
                                       'four_weeks': 2,
                                       'six_months': 2,
                                       'description': 'Received but not acknowledged'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'description': 'Acknowledged but not answered'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'description': 'Question answered'}]
            self.assertEqual(resp.context['questions_by_status'], expected_status_counts)

    def test_summary_page_applies_problem_category_filter(self):
        for url in self.urls:
            resp = self.client.get(url + '?problems_category=cleanliness')
            self.assertEqual(resp.context['problems_category'], 'cleanliness')
            self.assertEqual(len(resp.context['problems']), 1)
            self.assertEqual(resp.context['problems'][0].id, self.cleanliness_problem.id)
            self.assertEqual(resp.context['problems_total'], {'week': 1, 'four_weeks': 1, 'six_months': 1})
            expected_status_counts = [{'week': 1,
                                       'four_weeks': 1,
                                       'six_months': 1,
                                       'description': 'Received but not acknowledged'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'description': 'Acknowledged but not addressed'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'description': 'Addressed - problem solved'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'description': 'Addressed - unable to solve'}]
            self.assertEqual(resp.context['problems_by_status'], expected_status_counts)

    def test_summary_page_applies_question_category_filter(self):
        for url in self.urls:
            resp = self.client.get(url + '?questions_category=services')
            self.assertEqual(resp.context['questions_category'], 'services')
            self.assertEqual(len(resp.context['questions']), 1)
            self.assertEqual(resp.context['questions'][0].id, self.services_question.id)
            expected_status_counts = [{'week': 1,
                                       'four_weeks': 1,
                                       'six_months': 1,
                                       'description': 'Received but not acknowledged'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'description': 'Acknowledged but not answered'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'description': 'Question answered'}]
            self.assertEqual(resp.context['questions_by_status'], expected_status_counts)


    def test_public_summary_page_links_to_public_problems_and_questions(self):
        resp = self.client.get(self.public_summary_url)
        self.assertContains(resp, '/choices/problem/%s' % self.staff_problem.id )
        self.assertContains(resp, '/choices/question/%s' % self.general_question.id)

    def test_private_summary_page_links_to_private_problems_and_questions(self):
        resp = self.client.get(self.private_summary_url)
        self.assertTrue('/private/response' in resp.content)

class OrganisationDashboardTests(MockedChoicesAPITest):

    def setUp(self):
        super(OrganisationDashboardTests, self).setUp()
        self.dashboard_url = '/private/dashboard/gppractices/12702'

    def test_dashboard_page_exists(self):
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_page_shows_organisation_name(self):
        resp = self.client.get(self.dashboard_url)
        self.assertTrue('Test Organisation Name Dashboard' in resp.content)

class ResponseFormTests(TestCase):

    def setUp(self):
        self.problem = create_test_instance(Problem, {})
        self.response_form_url = '/private/response/problem/%s' % self.problem.id

    def test_response_page_exists(self):
        resp = self.client.get(self.response_form_url)
        self.assertEqual(resp.status_code, 200)

class ResponseConfirmTests(TestCase):

    def setUp(self):
        self.response_confirm_url = '/private/response-confirm'

    def test_response_page_exists(self):
        resp = self.client.get(self.response_confirm_url)
        self.assertEqual(resp.status_code, 200)

class OrganisationMapTests(MockedChoicesAPITest):

    @classmethod
    def setUpClass(cls):
        cls._organisations_path = os.path.abspath(organisations.__path__[0])
        cls._organisations_no_issues_json = open(os.path.join(cls._organisations_path, 'fixtures', 'map_expected_orgs_no_issues.json')).read()
        cls._organisations_issues_json = open(os.path.join(cls._organisations_path, 'fixtures', 'map_expected_orgs_with_issues.json')).read()
        cls._organisations_closed_issues_json = open(os.path.join(cls._organisations_path, 'fixtures', 'map_expected_orgs_with_closed_issues.json')).read()

    def setUp(self):
        super(OrganisationMapTests, self).setUp()
        self.map_url = '/choices/stats/map'

    def test_map_page_exists(self):
        resp = self.client.get(self.map_url)
        self.assertEqual(resp.status_code, 200)

    def test_organisations_json_displayed(self):
        resp = self.client.get(self.map_url)
        self.assertEqual(resp.context['organisations'], self._organisations_no_issues_json)

    def test_problems_and_questions_in_json(self):
        # Add some problem and questions into the db
        create_test_instance(Problem, {'organisation_type': 'hospitals', 'choices_id': 18444})
        create_test_instance(Problem, {'organisation_type': 'gppractices', 'choices_id': 12702})
        create_test_instance(Question, {'organisation_type': 'gppractices', 'choices_id': 12702})
        create_test_instance(Question, {'organisation_type': 'hospitals', 'choices_id': 18444})
        resp = self.client.get(self.map_url)
        self.assertEqual(resp.context['organisations'], self._organisations_issues_json)

    def test_closed_problems_not_in_json(self):
        create_test_instance(Problem, {'organisation_type': 'hospitals', 'choices_id': 18444})
        create_test_instance(Problem, {'organisation_type': 'gppractices', 'choices_id': 12702, 'status': Problem.RESOLVED})
        create_test_instance(Problem, {'organisation_type': 'gppractices', 'choices_id': 12702, 'status': Problem.NOT_RESOLVED})
        create_test_instance(Question, {'organisation_type': 'gppractices', 'choices_id': 12702})
        create_test_instance(Question, {'organisation_type': 'gppractices', 'choices_id': 12702, 'status':Question.RESOLVED})
        resp = self.client.get(self.map_url)
        self.assertEqual(resp.context['organisations'], self._organisations_closed_issues_json)

