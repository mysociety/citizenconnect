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
        self.summary_url = '/choices/stats/summary/gppractices/12702'

    def test_summary_page_exists(self):
        resp = self.client.get(self.summary_url)
        self.assertEqual(resp.status_code, 200)

    def test_summary_page_shows_organisation_name(self):
        resp = self.client.get(self.summary_url)
        self.assertTrue('Test Organisation Name Outcomes' in resp.content)

    def test_summary_page_has_problems(self):
        resp = self.client.get(self.summary_url)
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
        resp = self.client.get(self.summary_url)
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
        resp = self.client.get(self.summary_url + '?problems_category=cleanliness')
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
        resp = self.client.get(self.summary_url + '?questions_category=services')
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


class OrganisationDashboardTests(MockedChoicesAPITest):

    def setUp(self):
        super(OrganisationDashboardTests, self).setUp()
        self.summary_url = '/choices/stats/dashboard/gppractices/12702'

    def test_dashboard_page_exists(self):
        resp = self.client.get(self.summary_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_page_shows_organisation_name(self):
        resp = self.client.get(self.summary_url)
        self.assertTrue('Test Organisation Name Dashboard' in resp.content)
