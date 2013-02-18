import os
from mock import MagicMock, patch
import json
import urllib

# Django imports
from django.test import TestCase
from django.contrib.gis.geos import Point

# App imports
from problems.models import Problem
from questions.models import Question
import organisations

from ..models import Organisation
from . import create_test_instance, create_test_organisation

class OrganisationSummaryTests(TestCase):

    def setUp(self):
        # Make an organisation
        self.organisation = create_test_organisation()
        atts = {'organisation': self.organisation}
        atts.update({'category': 'cleanliness'})
        self.cleanliness_problem = create_test_instance(Problem, atts)
        atts.update({'category': 'staff'})
        self.staff_problem = create_test_instance(Problem, atts)
        atts.update({'category': 'services'})
        self.services_question = create_test_instance(Question, atts)
        atts.update({'category': 'general'})
        self.general_question = create_test_instance(Question, atts)
        self.public_summary_url = '/choices/stats/summary/%s' % self.organisation.ods_code
        self.private_summary_url = '/private/summary/%s' % self.organisation.ods_code
        self.urls = [self.public_summary_url, self.private_summary_url]

    def test_summary_page_exists(self):
        for url in self.urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_summary_page_shows_organisation_name(self):
        for url in self.urls:
            resp = self.client.get(url)
            self.assertTrue(self.organisation.name in resp.content)

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

class OrganisationDashboardTests(TestCase):

    def setUp(self):
        # Make an organisation
        self.organisation = create_test_organisation()
        self.dashboard_url = '/private/dashboard/%s' % self.organisation.ods_code

    def test_dashboard_page_exists(self):
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_page_shows_organisation_name(self):
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(self.organisation.name in resp.content)

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

class ResponseConfirmTests(TestCase):

    def setUp(self):
        self.response_confirm_url = '/private/response-confirm'

    def test_response_page_exists(self):
        resp = self.client.get(self.response_confirm_url)
        self.assertEqual(resp.status_code, 200)

class OrganisationMapTests(TestCase):

    def setUp(self):
        self.hospital = create_test_organisation({
            'organisation_type': 'hospitals',
            'choices_id': 18444,
            'ods_code': 'DEF456'
        })
        self.gp = create_test_organisation({'organisation_type':'gppractices'})
        self.map_url = '/choices/stats/map'

    def test_map_page_exists(self):
        resp = self.client.get(self.map_url)
        self.assertEqual(resp.status_code, 200)

    def test_organisations_json_displayed(self):
        # Set some dummy data
        resp = self.client.get(self.map_url)
        response_json = json.loads(resp.context['organisations'])
        self.assertEqual(len(response_json), 2)
        self.assertEqual(response_json[0]['ods_code'], self.hospital.ods_code)
        self.assertEqual(response_json[0]['issues'], [])
        self.assertEqual(response_json[1]['ods_code'], self.gp.ods_code)
        self.assertEqual(response_json[1]['issues'], [])

    def test_problems_and_questions_in_json(self):
        # Add some problem and questions into the db
        create_test_instance(Problem, {'organisation': self.hospital})
        create_test_instance(Problem, {'organisation': self.gp})
        create_test_instance(Question, {'organisation': self.gp})
        create_test_instance(Question, {'organisation': self.hospital})
        resp = self.client.get(self.map_url)
        response_json = json.loads(resp.context['organisations'])
        self.assertEqual(len(response_json[0]['issues']), 2)
        self.assertEqual(len(response_json[1]['issues']), 2)

    def test_closed_problems_not_in_json(self):
        create_test_instance(Problem, {'organisation': self.hospital})
        create_test_instance(Problem, {'organisation': self.gp, 'status': Problem.RESOLVED})
        create_test_instance(Problem, {'organisation': self.gp, 'status': Problem.NOT_RESOLVED})
        create_test_instance(Question, {'organisation': self.gp})
        create_test_instance(Question, {'organisation': self.gp, 'status':Question.RESOLVED})
        resp = self.client.get(self.map_url)
        response_json = json.loads(resp.context['organisations'])
        self.assertEqual(len(response_json[0]['issues']), 1)
        self.assertEqual(len(response_json[1]['issues']), 1)

def SummaryTests(TestCase):

    def setUp(self):
        super(SummaryTests, self).setUp()
        self.summary_url = '/choices/stats/summary'

    def test_summary_page_exists(self):
        resp = self.client.get(self.summary_url)
        self.assertEqual(resp.status_code, 200)

class ProviderPickerTests(TestCase):

    def setUp(self):
        self._organisations_path = os.path.abspath(organisations.__path__[0])
        mapit_example = open(os.path.join(self._organisations_path,
                                          'fixtures',
                                          'mapit_api',
                                          'SW1A1AA.json'))
        urllib.urlopen = MagicMock(return_value=mapit_example)
        self.nearby_gp = create_test_organisation({
            'name': 'Nearby GP',
            'organisation_type': 'gppractices',
            'point': Point(-0.13, 51.5)
        })
        self.faraway_gp = create_test_organisation({
            'name': 'Far GP',
            'organisation_type': 'gppractices',
            'point': Point(-0.15, 51.4)
        })
        self.base_url = "/choices/stats/pick-provider"
        self.results_url = "%s?organisation_type=gppractices&location=SW1A+1AA" % self.base_url

    def test_results_page_exists(self):
        resp = self.client.get(self.results_url)
        self.assertEqual(resp.status_code, 200)

    def test_results_page_shows_nearby_organisation(self):
        resp = self.client.get(self.results_url)
        self.assertContains(resp, self.nearby_gp.name, count=1, status_code=200)

    def test_results_page_does_not_show_far_away_organisation(self):
        resp = self.client.get(self.results_url)
        self.assertNotContains(resp, self.faraway_gp.name, status_code=200)

    def test_results_page_shows_organisation_by_name(self):
        resp = self.client.get("%s?organisation_type=gppractices&location=nearby" % self.base_url)
        self.assertContains(resp, self.nearby_gp.name, count=1, status_code=200)

    def test_results_page_does_not_show_organisation_with_other_name(self):
        resp = self.client.get("%s?organisation_type=gppractices&location=nearby" % self.base_url)
        self.assertNotContains(resp, self.faraway_gp.name, status_code=200)

    def test_validates_location_present(self):
        resp = self.client.get("%s?organisation_type=gppractices&location=" % self.base_url)
        self.assertContains(resp, 'Please enter a location', count=1, status_code=200)

    def test_shows_message_on_no_results(self):
        resp = self.client.get("%s?organisation_type=gppractices&location=non-existent" % self.base_url)
        self.assertContains(resp, "We couldn&#39;t find any matches", count=1, status_code=200)
