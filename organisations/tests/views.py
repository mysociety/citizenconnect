import os
from mock import Mock, MagicMock, patch
import json
import urllib

# Django imports
from django.test import TestCase
from django.contrib.gis.geos import Point

# App imports
from issues.models import Problem, Question

import organisations
from ..models import Organisation
from . import create_test_instance, create_test_organisation, create_test_service

class OrganisationSummaryTests(TestCase):

    def setUp(self):
        # Make an organisation
        self.organisation = create_test_organisation()
        self.service = create_test_service({'organisation': self.organisation})
        atts = {'organisation': self.organisation}
        atts.update({'category': 'cleanliness'})
        self.cleanliness_problem = create_test_instance(Problem, atts)
        atts.update({'category': 'staff'})
        self.staff_problem = create_test_instance(Problem, atts)
        atts.update({'category': 'other', 'service_id' : self.service.id})
        self.other_dept_problem = create_test_instance(Problem, atts)
        atts = {'organisation': self.organisation}
        atts.update({'category': 'services'})
        self.services_question = create_test_instance(Question, atts)
        atts.update({'category': 'general'})
        self.general_question = create_test_instance(Question, atts)
        atts.update({'category': 'appointments', 'service_id': self.service.id})
        self.appointment_dept_question = create_test_instance(Question, atts)

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
            self.assertEqual(len(resp.context['problems']), 3)
            self.assertEqual(resp.context['problems'][0].id, self.other_dept_problem.id)
            self.assertEqual(resp.context['problems'][1].id, self.staff_problem.id)
            self.assertEqual(resp.context['problems'][2].id, self.cleanliness_problem.id)
            expected_total_counts = {'week': 3, 'four_weeks': 3, 'six_months': 3, 'all_time': 3}
            self.assertEqual(resp.context['problems_total'], expected_total_counts)
            expected_status_counts = [{'week': 3,
                                       'four_weeks': 3,
                                       'six_months': 3,
                                       'all_time': 3,
                                       'description': 'Received but not acknowledged'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'all_time': 0,
                                       'description': 'Acknowledged but not addressed'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'all_time': 0,
                                       'description': 'Addressed - problem solved'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'all_time': 0,
                                       'description': 'Addressed - unable to solve'}]
            self.assertEqual(resp.context['problems_by_status'], expected_status_counts)

    def test_summary_page_has_questions(self):
        for url in self.urls:
            resp = self.client.get(url)
            self.assertEqual(len(resp.context['questions']), 3)
            self.assertEqual(resp.context['questions'][0].id, self.appointment_dept_question.id)
            self.assertEqual(resp.context['questions'][1].id, self.general_question.id)
            self.assertEqual(resp.context['questions'][2].id, self.services_question.id)
            expected_status_counts = [{'week': 3,
                                       'four_weeks': 3,
                                       'six_months': 3,
                                       'all_time': 3,
                                       'description': 'Received but not acknowledged'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'all_time': 0,
                                       'description': 'Acknowledged but not answered'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'all_time': 0,
                                       'description': 'Question answered'}]
            self.assertEqual(resp.context['questions_by_status'], expected_status_counts)

    def test_summary_page_applies_problem_category_filter(self):
        for url in self.urls:
            resp = self.client.get(url + '?problems_category=cleanliness')
            self.assertEqual(resp.context['problems_category'], 'cleanliness')
            self.assertEqual(len(resp.context['problems']), 1)
            self.assertEqual(resp.context['problems'][0].id, self.cleanliness_problem.id)
            expected_total_counts = {'week': 1, 'four_weeks': 1, 'six_months': 1, 'all_time': 1}
            self.assertEqual(resp.context['problems_total'], expected_total_counts)
            expected_status_counts = [{'week': 1,
                                       'four_weeks': 1,
                                       'six_months': 1,
                                       'all_time': 1,
                                       'description': 'Received but not acknowledged'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'all_time': 0,
                                       'description': 'Acknowledged but not addressed'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'all_time': 0,
                                       'description': 'Addressed - problem solved'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'all_time': 0,
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
                                       'all_time': 1,
                                       'description': 'Received but not acknowledged'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'all_time': 0,
                                       'description': 'Acknowledged but not answered'},
                                      {'week': 0,
                                       'four_weeks': 0,
                                       'six_months': 0,
                                       'all_time': 0,
                                       'description': 'Question answered'}]
            self.assertEqual(resp.context['questions_by_status'], expected_status_counts)

    def test_summary_page_applies_department_filter(self):
        for url in self.urls:
            resp = self.client.get(url + '?service=%s' % self.service.id)
            self.assertEqual(resp.context['selected_service'], self.service.id)
            self.assertEqual(len(resp.context['questions']), 1)
            self.assertEqual(len(resp.context['problems']), 1)
            self.assertEqual(resp.context['questions'][0].id, self.appointment_dept_question.id)
            self.assertEqual(resp.context['problems'][0].id, self.other_dept_problem.id)
            expected_question_status_counts = [{'week': 1,
                                               'four_weeks': 1,
                                               'six_months': 1,
                                               'all_time': 1,
                                               'description': 'Received but not acknowledged'},
                                              {'week': 0,
                                               'four_weeks': 0,
                                               'six_months': 0,
                                               'all_time': 0,
                                               'description': 'Acknowledged but not answered'},
                                              {'week': 0,
                                               'four_weeks': 0,
                                               'six_months': 0,
                                               'all_time': 0,
                                               'description': 'Question answered'}]
            expected_problem_status_counts = [{'week': 1,
                                              'four_weeks': 1,
                                              'six_months': 1,
                                              'all_time': 1,
                                              'description': 'Received but not acknowledged'},
                                             {'week': 0,
                                              'four_weeks': 0,
                                              'six_months': 0,
                                              'all_time': 0,
                                              'description': 'Acknowledged but not addressed'},
                                             {'week': 0,
                                              'four_weeks': 0,
                                              'six_months': 0,
                                              'all_time': 0,
                                              'description': 'Addressed - problem solved'},
                                             {'week': 0,
                                              'four_weeks': 0,
                                              'six_months': 0,
                                              'all_time': 0,
                                              'description': 'Addressed - unable to solve'}]
            self.assertEqual(resp.context['questions_by_status'], expected_question_status_counts)
            self.assertEqual(resp.context['problems_by_status'], expected_problem_status_counts)

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

    def mock_api_response(self, data, response_code):
        mock_response = MagicMock()
        urllib.urlopen = mock_response
        instance = mock_response.return_value
        instance.read.return_value = data
        instance.getcode.return_value = response_code

    def setUp(self):
        self._organisations_path = os.path.abspath(organisations.__path__[0])
        self.mapit_example = open(os.path.join(self._organisations_path,
                                          'fixtures',
                                          'mapit_api',
                                          'SW1A1AA.json')).read()

        self. mock_api_response(self.mapit_example, 200)
        self.nearby_gp = create_test_organisation({
            'name': 'Nearby GP',
            'organisation_type': 'gppractices',
            'ods_code':'ABC123',
            'point': Point(-0.13, 51.5)
        })
        self.faraway_gp = create_test_organisation({
            'name': 'Far GP',
            'organisation_type': 'gppractices',
            'ods_code':'DEF456',
            'point': Point(-0.15, 51.4)
        })
        self.nearby_hospital = create_test_organisation({
            'name': 'Nearby Hospital',
            'organisation_type': 'hospitals',
            'ods_code':'HOS123',
            'point': Point(-0.13, 51.5)
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

    def test_results_filters_postcode_organisations_by_type(self):
        resp = self.client.get(self.results_url)
        self.assertNotContains(resp, self.nearby_hospital.name, status_code=200)

    def test_results_filters_name_organisations_by_type(self):
        resp = self.client.get("%s?organisation_type=gppractices&location=nearby" % self.base_url)
        self.assertNotContains(resp, self.nearby_hospital.name, status_code=200)

    def test_results_page_shows_paginator_for_over_ten_results(self):
        for i in range(12):
            create_test_organisation({
                'name': 'Multi GP',
                'organisation_type': 'gppractices',
                'ods_code':'ABC{0}'.format(i)
            })
        resp = self.client.get("%s?organisation_type=gppractices&location=multi" % self.base_url)
        self.assertContains(resp, 'Multi GP', count=10, status_code=200)
        self.assertContains(resp, 'next', count=1)

    def test_results_page_no_paginator_for_under_ten_results(self):
        for i in range(3):
            create_test_organisation({
                'name': 'Multi GP',
                'organisation_type': 'gppractices',
                'ods_code': 'DEF{0}'.format(i)
            })
        resp = self.client.get("%s?organisation_type=gppractices&location=multi" % self.base_url)
        self.assertContains(resp, 'Multi GP', count=3, status_code=200)
        self.assertNotContains(resp, 'next')

    def test_validates_location_present(self):
        resp = self.client.get("%s?organisation_type=gppractices&location=" % self.base_url)
        self.assertContains(resp, 'Please enter a location', count=1, status_code=200)

    def test_shows_message_on_no_results(self):
        resp = self.client.get("%s?organisation_type=gppractices&location=non-existent" % self.base_url)
        self.assertContains(resp, "We couldn&#39;t find any matches", count=1, status_code=200)

    def test_handles_the_case_where_the_mapit_api_cannot_be_connected_to(self):
        urllib.urlopen = MagicMock(side_effect=IOError('foo'))
        resp = self.client.get(self.results_url)
        expected_message = 'Sorry, our postcode lookup service is temporarily unavailable. Please try later or search by provider name'
        self.assertContains(resp, expected_message, count=1, status_code=200)

    def test_handes_the_case_where_the_mapit_api_returns_an_error_code(self):
        self.mock_api_response(self.mapit_example, 500)
        resp = self.client.get(self.results_url)
        expected_message = "Sorry, our postcode lookup service is temporarily unavailable. Please try later or search by provider name"
        self.assertContains(resp, expected_message, count=1, status_code=200)

    def test_handles_the_case_where_mapit_does_not_recognize_the_postcode_as_valid(self):
        self.mock_api_response(self.mapit_example, 400)
        resp = self.client.get(self.results_url)
        expected_message = "Sorry, that doesn&#39;t seem to be a valid postcode."
        self.assertContains(resp, expected_message, count=1, status_code=200)

    def test_handles_the_case_where_mapit_does_not_have_the_postcode(self):
        self.mock_api_response(self.mapit_example, 404)
        resp = self.client.get(self.results_url)
        expected_message = "Sorry, no postcode matches that query."
        self.assertContains(resp, expected_message, count=1, status_code=200)

    def test_shows_message_when_no_results_for_postcode(self):
        Organisation.objects.filter = MagicMock(return_value=[])
        resp = self.client.get(self.results_url)
        expected_message = 'Sorry, there are no matches within 5 miles of SW1A 1AA. Please try again'
        self.assertContains(resp, expected_message, count=1, status_code=200)

