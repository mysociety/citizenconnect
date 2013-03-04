import os
from mock import Mock, MagicMock, patch
import json
import urllib

# Django imports
from django.test import TestCase
from django.contrib.gis.geos import Point
from django.core.urlresolvers import reverse

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

        # Problems
        atts = {'organisation': self.organisation}
        atts.update({'category': 'cleanliness',
                     'happy_service': True,
                     'happy_outcome': None,
                     'acknowledged_in_time': True,
                     'addressed_in_time': True})
        self.cleanliness_problem = create_test_instance(Problem, atts)
        atts.update({'category': 'staff',
                     'happy_service': True,
                     'happy_outcome': True,
                     'acknowledged_in_time': None,
                     'addressed_in_time': None})
        self.staff_problem = create_test_instance(Problem, atts)
        atts.update({'category': 'other',
                     'service_id' : self.service.id,
                     'happy_service': False,
                     'happy_outcome': True,
                     'acknowledged_in_time': False,
                     'addressed_in_time': None})
        self.other_dept_problem = create_test_instance(Problem, atts)

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
            total = resp.context['problems_total']
            self.assertEqual(total['all_time'], 3)
            self.assertEqual(total['week'], 3)
            self.assertEqual(total['four_weeks'], 3)
            self.assertEqual(total['six_months'], 3)

            problems_by_status = resp.context['problems_by_status']
            self.assertEqual(problems_by_status[0]['all_time'], 3)
            self.assertEqual(problems_by_status[0]['week'], 3)
            self.assertEqual(problems_by_status[0]['four_weeks'], 3)
            self.assertEqual(problems_by_status[0]['six_months'], 3)
            self.assertEqual(problems_by_status[0]['description'], 'Received but not acknowledged')

            self.assertEqual(problems_by_status[1]['all_time'], 0)
            self.assertEqual(problems_by_status[1]['week'], 0)
            self.assertEqual(problems_by_status[1]['four_weeks'], 0)
            self.assertEqual(problems_by_status[1]['six_months'], 0)
            self.assertEqual(problems_by_status[1]['description'], 'Acknowledged but not addressed')

            self.assertEqual(problems_by_status[2]['all_time'], 0)
            self.assertEqual(problems_by_status[2]['week'], 0)
            self.assertEqual(problems_by_status[2]['four_weeks'], 0)
            self.assertEqual(problems_by_status[2]['six_months'], 0)
            self.assertEqual(problems_by_status[2]['description'], 'Addressed - problem solved')

            self.assertEqual(problems_by_status[3]['all_time'], 0)
            self.assertEqual(problems_by_status[3]['week'], 0)
            self.assertEqual(problems_by_status[3]['four_weeks'], 0)
            self.assertEqual(problems_by_status[3]['six_months'], 0)
            self.assertEqual(problems_by_status[3]['description'], 'Addressed - unable to solve')

    def test_summary_page_applies_problem_category_filter(self):
        for url in self.urls:
            resp = self.client.get(url + '?problems_category=cleanliness')
            self.assertEqual(resp.context['problems_category'], 'cleanliness')
            total = resp.context['problems_total']
            self.assertEqual(total['all_time'], 1)
            self.assertEqual(total['week'], 1)
            self.assertEqual(total['four_weeks'], 1)
            self.assertEqual(total['six_months'], 1)

            problems_by_status = resp.context['problems_by_status']
            self.assertEqual(problems_by_status[0]['all_time'], 1)
            self.assertEqual(problems_by_status[0]['week'], 1)
            self.assertEqual(problems_by_status[0]['four_weeks'], 1)
            self.assertEqual(problems_by_status[0]['six_months'], 1)

    def test_summary_page_applies_department_filter(self):
        for url in self.urls:
            resp = self.client.get(url + '?service=%s' % self.service.id)
            self.assertEqual(resp.context['selected_service'], self.service.id)

            problems_by_status = resp.context['problems_by_status']
            self.assertEqual(problems_by_status[0]['all_time'], 1)
            self.assertEqual(problems_by_status[0]['week'], 1)
            self.assertEqual(problems_by_status[0]['four_weeks'], 1)
            self.assertEqual(problems_by_status[0]['six_months'], 1)

    def test_summary_page_gets_survey_data(self):
        for url in self.urls:
            resp = self.client.get(url)
            issues_total = resp.context['issues_total']
            self.assertEqual(issues_total['happy_service'], 0.666666666666667)
            self.assertEqual(issues_total['happy_outcome'], 1.0)

    def test_summary_page_gets_time_limit_data(self):
        for url in self.urls:
            resp = self.client.get(url)
            issues_total = resp.context['issues_total']
            self.assertEqual(issues_total['acknowledged_in_time'], 0.5)
            self.assertEqual(issues_total['addressed_in_time'], 1.0)

class OrganisationProblemsTests(TestCase):

    def setUp(self):
        self.hospital = create_test_organisation({'organisation_type': 'hospitals',
                                                  'ods_code': 'ABC123'})
        self.gp = create_test_organisation({'organisation_type': 'gppractices',
                                            'ods_code': 'DEF456'})
        self.public_hospital_problems_url = '/choices/stats/problems/%s' % self.hospital.ods_code
        self.private_hospital_problems_url = '/private/problems/%s' % self.hospital.ods_code
        self.public_gp_problems_url = '/choices/stats/problems/%s' % self.gp.ods_code
        self.private_gp_problems_url = '/private/problems/%s' % self.gp.ods_code
        self.staff_problem = create_test_instance(Problem, {'category': 'staff',
                                                            'organisation': self.hospital})

    def test_shows_services_for_hospitals(self):
        for url in [self.public_hospital_problems_url, self.private_hospital_problems_url]:
            resp = self.client.get(url)
            self.assertContains(resp, 'Department', count=1, status_code=200)

    def test_shows_time_limits_for_hospitals(self):
        for url in [self.public_hospital_problems_url, self.private_hospital_problems_url]:
            resp = self.client.get(url)
            self.assertContains(resp, 'Acknowledged In Time', count=1, status_code=200)
            self.assertContains(resp, 'Addressed In Time', count=1, status_code=200)

    def test_no_services_for_gps(self):
        for url in [self.public_gp_problems_url, self.private_gp_problems_url]:
            resp = self.client.get(url)
            self.assertNotContains(resp, 'Department')


    def test_no_time_limits_for_gps(self):
        for url in [self.public_gp_problems_url, self.private_gp_problems_url]:
            resp = self.client.get(url)
            self.assertNotContains(resp, 'Acknowledged In Time')
            self.assertNotContains(resp, 'Addressed In Time')

    def test_public_page_exists(self):
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertEqual(resp.status_code, 200)

    def test_public_page_links_to_public_problems(self):
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertContains(resp, '/choices/problem/%s' % self.staff_problem.id )

    def test_private_page_exists(self):
        resp = self.client.get(self.private_hospital_problems_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_page_links_to_problems(self):
        resp = self.client.get(self.private_hospital_problems_url)
        self.assertTrue('/private/response/problem/%s' % self.staff_problem.id in resp.content)

class OrganisationDashboardTests(TestCase):

    def setUp(self):
        # Make an organisation
        self.organisation = create_test_organisation()
        self.problem = create_test_instance(Problem, {'organisation': self.organisation})
        self.dashboard_url = '/private/dashboard/%s' % self.organisation.ods_code

    def test_dashboard_page_exists(self):
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_page_shows_organisation_name(self):
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(self.organisation.name in resp.content)

    def test_dashboard_shows_problems(self):
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(self.problem.summary in resp.content)

class OrganisationMapTests(TestCase):

    def setUp(self):
        self.hospital = create_test_organisation({
            'organisation_type': 'hospitals',
            'choices_id': 18444,
            'ods_code': 'DEF456'
        })
        self.gp = create_test_organisation({'organisation_type':'gppractices'})
        self.map_url = '/choices/stats/map'
        self.private_map_url = '/private/map'

    def test_map_page_exists(self):
        resp = self.client.get(self.map_url)
        self.assertEqual(resp.status_code, 200)

    def test_organisations_json_displayed(self):
        # Set some dummy data
        resp = self.client.get(self.map_url)
        response_json = json.loads(resp.context['organisations'])
        self.assertEqual(len(response_json), 2)
        self.assertEqual(response_json[0]['ods_code'], self.hospital.ods_code)
        self.assertEqual(response_json[0]['problems'], [])
        self.assertEqual(response_json[1]['ods_code'], self.gp.ods_code)
        self.assertEqual(response_json[1]['problems'], [])

    def test_problems_in_json(self):
        # Add some problem and questions into the db
        create_test_instance(Problem, {'organisation': self.hospital})
        create_test_instance(Problem, {'organisation': self.gp})

        resp = self.client.get(self.map_url)
        response_json = json.loads(resp.context['organisations'])

        self.assertEqual(len(response_json[0]['problems']), 1)
        self.assertEqual(len(response_json[1]['problems']), 1)

    def test_closed_problems_not_in_json(self):
        create_test_instance(Problem, {'organisation': self.hospital})
        create_test_instance(Problem, {'organisation': self.gp, 'status': Problem.RESOLVED})
        create_test_instance(Problem, {'organisation': self.gp, 'status': Problem.NOT_RESOLVED})

        resp = self.client.get(self.map_url)
        response_json = json.loads(resp.context['organisations'])

        self.assertEqual(len(response_json[0]['problems']), 1)
        self.assertEqual(len(response_json[1]['problems']), 0)

    def test_public_map_provider_urls_are_to_public_summary_pages(self):
        expected_hospital_url = reverse('public-org-summary', kwargs={'ods_code':self.hospital.ods_code, 'cobrand':'choices'})
        expected_gp_url = reverse('public-org-summary', kwargs={'ods_code':self.gp.ods_code, 'cobrand':'choices'})

        resp = self.client.get(self.map_url)
        response_json = json.loads(resp.context['organisations'])

        self.assertEqual(response_json[0]['url'], expected_hospital_url)
        self.assertEqual(response_json[1]['url'], expected_gp_url)

    def test_private_map_page_exists(self):
        resp = self.client.get(self.private_map_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_map_provider_urls_are_to_private_dashboards(self):
        expected_hospital_url = reverse('org-dashboard', kwargs={'ods_code':self.hospital.ods_code})
        expected_gp_url = reverse('org-dashboard', kwargs={'ods_code':self.gp.ods_code})

        resp = self.client.get(self.private_map_url)
        response_json = json.loads(resp.context['organisations'])

        self.assertEqual(response_json[0]['url'], expected_hospital_url)
        self.assertEqual(response_json[1]['url'], expected_gp_url)

class SummaryTests(TestCase):

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

    def test_handles_the_case_where_the_mapit_api_returns_an_error_code(self):
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

