# encoding: utf-8
import os
from mock import MagicMock
import json
import urllib
import logging
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait

# Django imports
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.gis.geos import Point
from django.core.urlresolvers import reverse
from django.utils.timezone import utc


# App imports
from citizenconnect.browser_testing import SeleniumTestCase
from issues.models import Problem

import organisations
from ..models import Organisation
from ..forms import MapitPostCodeLookup, MapitPostcodeNotFoundError
from ..views.base import Summary
from . import (create_test_problem,
               create_test_organisation,
               create_test_service,
               create_test_review,
               AuthorizationTestCase)
from organisations.forms import OrganisationFinderForm
from geocoder.models import Place


class OrganisationMapTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationMapTests, self).setUp()
        self.hospital = self.test_hospital
        self.other_gp = self.test_gp_branch
        self.map_url = reverse('org-map', kwargs={'cobrand': 'choices'})

    def test_map_page_exists(self):
        resp = self.client.get(self.map_url)
        self.assertEqual(resp.status_code, 200)

    def test_organisations_json_displayed(self):
        # Set some dummy data
        resp = self.client.get(self.map_url)
        response_json = json.loads(resp.context['organisations'])
        self.assertEqual(len(response_json), 2)
        self.assertEqual(response_json[0]['ods_code'], self.other_gp.ods_code)
        self.assertEqual(response_json[0]['all_time_open'], 0)
        self.assertEqual(response_json[1]['ods_code'], self.hospital.ods_code)
        self.assertEqual(response_json[1]['all_time_open'], 0)

    def test_public_map_doesnt_include_rejected_or_hidden_status_problems(self):
        # These problems should show up
        # A brand new un-moderated problem
        create_test_problem({'organisation': self.other_gp})
        # A problem the moderator has accepted
        create_test_problem({'organisation': self.hospital,
                            'publication_status': Problem.PUBLISHED})

        # These problems should not be shown
        # A problem the moderator has rejected
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.REJECTED})
        # A problem the moderator has accepted, but a organisation parent user has said
        # is abusive/vexatious (possibly because it's a dupe)
        create_test_problem({'organisation': self.other_gp,
                             'publication_status': Problem.PUBLISHED,
                             'status': Problem.ABUSIVE})

        resp = self.client.get(self.map_url)
        response_json = json.loads(resp.context['organisations'])
        self.assertEqual(response_json[0]['all_time_open'], 1)
        self.assertEqual(response_json[1]['all_time_open'], 1)

    def test_public_map_provider_urls_are_to_public_summary_pages(self):
        expected_hospital_url = reverse('public-org-summary', kwargs={'ods_code': self.hospital.ods_code,
                                                                      'cobrand': 'choices'})
        expected_gp_url = reverse('public-org-summary', kwargs={'ods_code': self.other_gp.ods_code,
                                                                'cobrand': 'choices'})

        resp = self.client.get(self.map_url)
        response_json = json.loads(resp.context['organisations'])

        self.assertEqual(response_json[0]['url'], expected_gp_url)
        self.assertEqual(response_json[1]['url'], expected_hospital_url)

    def test_map_filters_by_organisation_type(self):
        org_type_filtered_url = "{0}?organisation_type=hospitals".format(self.map_url)

        resp = self.client.get(org_type_filtered_url)
        response_json = json.loads(resp.context['organisations'])
        self.assertEqual(len(response_json), 1)
        self.assertEqual(response_json[0]['ods_code'], self.hospital.ods_code)
        self.assertEqual(response_json[0]['all_time_open'], 0)

    def test_map_filters_by_service(self):
        # Create some problems to filter
        service = create_test_service({"organisation": self.hospital})
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'service': service})
        create_test_problem({'organisation': self.other_gp,
                             'publication_status': Problem.PUBLISHED})

        service_filtered_url = "{0}?service_code={1}".format(self.map_url, service.service_code)

        resp = self.client.get(service_filtered_url)
        response_json = json.loads(resp.context['organisations'])
        self.assertEqual(len(response_json), 2)
        self.assertEqual(response_json[0]['ods_code'], self.other_gp.ods_code)
        self.assertEqual(response_json[0]['all_time_open'], 0)
        self.assertEqual(response_json[1]['ods_code'], self.hospital.ods_code)
        self.assertEqual(response_json[1]['all_time_open'], 1)

    def test_map_filters_by_category(self):
        # Create some problems to filter
        create_test_problem({'organisation': self.other_gp,
                             'publication_status': Problem.PUBLISHED,
                             'category': 'staff'})
        create_test_problem({'organisation': self.other_gp,
                             'publication_status': Problem.PUBLISHED,
                             'category': 'cleanliness'})

        category_filtered_url = "{0}?category=staff".format(self.map_url)

        resp = self.client.get(category_filtered_url)
        response_json = json.loads(resp.context['organisations'])
        self.assertEqual(len(response_json), 2)
        self.assertEqual(response_json[0]['ods_code'], self.other_gp.ods_code)
        self.assertEqual(response_json[0]['all_time_open'], 1)
        self.assertEqual(response_json[1]['ods_code'], self.hospital.ods_code)
        self.assertEqual(response_json[1]['all_time_open'], 0)

    def test_map_filters_by_status(self):
        # Create some problems to filter
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'status': Problem.NEW})
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'status': Problem.ACKNOWLEDGED})

        status_filtered_url = "{0}?status={1}".format(self.map_url, Problem.ACKNOWLEDGED)

        resp = self.client.get(status_filtered_url)
        response_json = json.loads(resp.context['organisations'])
        self.assertEqual(len(response_json), 2)
        self.assertEqual(response_json[0]['ods_code'], self.other_gp.ods_code)
        self.assertEqual(response_json[0]['all_time_open'], 0)
        self.assertEqual(response_json[1]['ods_code'], self.hospital.ods_code)
        self.assertEqual(response_json[1]['all_time_open'], 1)

    def test_map_returns_json_when_asked(self):
        json_url = "{0}?format=json".format(self.map_url)
        resp = self.client.get(json_url)
        self.assertEqual(resp['Content-Type'], 'application/json')
        response_json = json.loads(resp.content)
        self.assertEqual(len(response_json), 2)
        self.assertEqual(response_json[0]['ods_code'], self.other_gp.ods_code)
        self.assertEqual(response_json[0]['all_time_open'], 0)
        self.assertEqual(response_json[1]['ods_code'], self.hospital.ods_code)
        self.assertEqual(response_json[1]['all_time_open'], 0)

    def test_map_returns_json_for_orgs_within_bounds(self):
        # Create an org inside the bounds
        create_test_organisation({'point': Point(0.0, 0.0), 'ods_code': 'XYZ987'})
        # Create an org outside the bounds
        create_test_organisation({'point': Point(1.0, 1.0), 'ods_code': 'XYZ988'})
        json_url = "{0}?format=json&bounds[]=-0.1&bounds[]=-0.1&bounds[]=0.1&bounds[]=0.1".format(self.map_url)
        resp = self.client.get(json_url)
        self.assertEqual(resp['Content-Type'], 'application/json')
        response_json = json.loads(resp.content)
        self.assertEqual(len(response_json), 1)


class MapOrganisationCoordsTests(TestCase):
    def setUp(self):
        self.test_org = create_test_organisation()
        self.map_org_url = reverse('org-coords-map', kwargs={'cobrand': 'choices', 'ods_code': self.test_org.ods_code})

    def test_single_map_org_page_exists(self):
        resp = self.client.get(self.map_org_url)
        self.assertEqual(200, resp.status_code)

    def test_org_not_found_raises_404(self):
        non_existent_org_url = reverse(
            'org-coords-map',
            kwargs={'cobrand': 'choices', 'ods_code': '404'}
        )
        # disable logging of "Not Found"
        logger = logging.getLogger('django.request')
        previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        resp = self.client.get(non_existent_org_url)

        # restore logger
        logger.setLevel(previous_level)
        self.assertEqual(404, resp.status_code)


class MapSearchTests(TestCase):
    def setUp(self):
        self.place_search_url = reverse('org-map-search', kwargs={'cobrand': 'choices'})
        # Mock out mapit
        self._old_postcode_to_point = MapitPostCodeLookup.postcode_to_point
        MapitPostCodeLookup.postcode_to_point = MagicMock()

    def tearDown(self):
        MapitPostCodeLookup.postcode_to_point = self._old_postcode_to_point

    def test_search_page_exists(self):
        resp = self.client.get(self.place_search_url)
        self.assertEqual(200, resp.status_code)

    def test_no_search_term_returns_no_results(self):
        resp = self.client.get(self.place_search_url + '?term=')
        self.assertEqual('[]', resp.content)

    def test_search_returns_organisations(self):
        org = create_test_organisation({'name': "Test Organisation"})
        resp = self.client.get(self.place_search_url + '?term=Tes')
        self.assertContains(resp, org.name)

    def test_search_returns_places(self):
        place = Place.objects.create(
            name='Place Name',
            context_name="Place Name, London",
            centre=Point(50, 2),
            source=Place.SOURCE_OS_LOCATOR,
        )
        resp = self.client.get(self.place_search_url + '?term=Pla')
        self.assertContains(resp, place.context_name)

    def test_search_returns_postcode(self):
        MapitPostCodeLookup.postcode_to_point.return_value = Point(-0.14158706711000901, 51.501009611553926)
        resp = self.client.get(self.place_search_url + '?term=SW1A+1AA')
        data = json.loads(resp.content)
        self.assertEqual(data, [{
            'id': 'SW1A1AA',
            'lat': 51.501009611553926,
            'lon': -0.14158706711000901,
            'text': 'SW1A 1AA (postcode)',
            'type': 'place',
        }])

    def test_search_returns_partial_postcode(self):
        MapitPostCodeLookup.postcode_to_point.return_value = Point(-0.13294453160162145, 51.501434410230779)
        resp = self.client.get(self.place_search_url + '?term=SW1A')
        data = json.loads(resp.content)
        self.assertEqual(data, [{
            'id': 'SW1A',
            'lat': 51.501434410230779,
            'lon': -0.13294453160162145,
            'text': 'SW1A (postcode)',
            'type': 'place',
        }])

    def test_search_returns_bad_postcode(self):
        MapitPostCodeLookup.postcode_to_point.side_effect = MapitPostcodeNotFoundError()
        resp = self.client.get(self.place_search_url + '?term=BA1D+1AB')
        data = json.loads(resp.content)
        self.assertEqual(data, [])


class OrganisationMapBrowserTests(SeleniumTestCase):

    def setUp(self):
        super(OrganisationMapBrowserTests, self).setUp()
        self.map_url = reverse('org-map', kwargs={'cobrand': 'choices'})

    def test_submit_button_hidden(self):
        self.driver.get(self.full_url(self.map_url))
        submit_button = self.driver.find_element_by_css_selector('.filters__button')
        self.assertFalse(submit_button.is_displayed())

    def test_filter_selection(self):
        self.driver.get(self.full_url(self.map_url))

        # Find the organisation type selector, and select hospitals
        org_type_filter = self.driver.find_element_by_id('id_organisation_type')
        org_type_filter.find_element_by_css_selector('option[value="hospitals"]').click()

        # Wait until it the select is re-enabled - this is a sign of a successful ajax request
        WebDriverWait(self.driver, 3).until(
            lambda x: org_type_filter.get_attribute('disabled') is None
        )

        # Check the select wrapper no longer has a --default class, so it looks selected
        org_type_filter_container = self.driver.find_element_by_css_selector('.filters .filters__dropdown')
        self.assertEqual(org_type_filter_container.get_attribute('class'), 'filters__dropdown')


@override_settings(SUMMARY_THRESHOLD=['all_time', 1])
class SummaryTests(AuthorizationTestCase):

    def setUp(self):
        super(SummaryTests, self).setUp()
        self.summary_url = reverse('org-all-summary', kwargs={'cobrand': 'choices'})
        create_test_problem({'organisation': self.test_hospital, 'category': 'staff'})
        create_test_problem({'organisation': self.test_gp_branch,
                             'publication_status': Problem.PUBLISHED,
                             'status': Problem.ABUSIVE,
                             'category': 'cleanliness'})
        create_test_review({'organisation': self.test_hospital,
                            'api_published': datetime.utcnow().replace(tzinfo=utc),
                            'api_updated': datetime.utcnow().replace(tzinfo=utc)})

    def test_summary_page_exists(self):
        resp = self.client.get(self.summary_url)
        self.assertEqual(resp.status_code, 200)

    def test_summary_page_shows_reviews(self):
        resp = self.client.get(self.summary_url)
        self.assertContains(resp, '<td class="reviews_all_time">1</td>', count=1, status_code=200)

    def test_summary_doesnt_include_hidden_status_problems_in_default_view(self):
        resp = self.client.get(self.summary_url)
        self.assertContains(resp, self.test_hospital.name)
        self.assertNotContains(resp, self.test_gp_branch.name)
        self.assertContains(resp, '<td class="all_time">1</td>', count=1, status_code=200)

    def test_status_filter_only_shows_visible_statuses_in_filters(self):
        resp = self.client.get(self.summary_url)
        for status in Problem.HIDDEN_STATUSES:
            self.assertNotContains(resp, Problem.STATUS_CHOICES[status][1])

    def test_summary_page_ignores_hidden_status_filter(self):
        resp = self.client.get(self.summary_url + '?status={0}'.format(Problem.ABUSIVE))
        self.assertContains(resp, self.test_hospital.name)
        self.assertNotContains(resp, self.test_gp_branch.name)
        self.assertContains(resp, '<td class="all_time">1</td>', count=1, status_code=200)

    def test_summary_page_applies_threshold_from_settings(self):
        with self.settings(SUMMARY_THRESHOLD=('six_months', 1)):
            resp = self.client.get(self.summary_url)
            self.assertContains(resp, self.test_hospital.name)

        with self.settings(SUMMARY_THRESHOLD=('six_months', 2)):
            resp = self.client.get(self.summary_url)
            self.assertNotContains(resp, self.test_hospital.name)

    def test_summary_page_filters_by_ccg(self):
        # Add an issue for other_test_organisation that won't be filtered because
        # of it's Hidden status, but will be by the other orgs ccg
        create_test_problem({'organisation': self.test_gp_branch})

        ccg_filtered_url = '{0}?ccg={1}'.format(self.summary_url, self.test_ccg.id)
        resp = self.client.get(ccg_filtered_url)
        self.assertContains(resp, self.test_hospital.name)
        self.assertNotContains(resp, self.test_gp_branch.name)

    def test_summary_page_filters_by_organisation_type(self):
        # Add an issue for other_test_organisation that won't be filtered because
        # of it's Hidden status but will be by the org_type filter
        create_test_problem({'organisation': self.test_gp_branch})

        org_type_filtered_url = '{0}?organisation_type=hospitals'.format(self.summary_url)
        resp = self.client.get(org_type_filtered_url)
        self.assertContains(resp, self.test_hospital.name)
        self.assertNotContains(resp, self.test_gp_branch.name)

    def test_summary_page_filters_by_category(self):
        # Add an issue for other_test_organisation that won't be filtered because
        # of it's Hidden status but will be filtered by our category
        create_test_problem({'organisation': self.test_gp_branch,
                             'category': 'cleanliness'})

        category_filtered_url = '{0}?category=staff'.format(self.summary_url)
        resp = self.client.get(category_filtered_url)
        self.assertContains(resp, self.test_hospital.name)
        # NOTE: we rely on the SUMMARY_THRESHOLD setting to make this org disappear
        self.assertNotContains(resp, self.test_gp_branch.name)

    def test_summary_page_filters_by_status(self):
        # Add an issue for other_test_organisation that won't be filtered because
        # of it's Hidden status, but should be filtered by our status filter
        create_test_problem({'organisation': self.test_gp_branch,
                             'status': Problem.ACKNOWLEDGED})

        status_filtered_url = '{0}?status={1}'.format(self.summary_url, Problem.NEW)
        resp = self.client.get(status_filtered_url)
        self.assertContains(resp, self.test_hospital.name)
        # NOTE: we rely on the SUMMARY_THRESHOLD setting to make this org disappear
        self.assertNotContains(resp, self.test_gp_branch.name)

    def test_public_summary_page_does_not_have_breach_filter(self):
        resp = self.client.get(self.summary_url)
        self.assertNotContains(resp, '<select name="breach" id="id_breach">')

    def test_public_summary_accepts_interval_parameters(self):
        resp = self.client.get("{0}?problems_interval=week&reviews_interval=reviews_week".format(self.summary_url))
        self.assertEqual(resp.context['problems_sort_column'], resp.context['table'].columns['week'])
        self.assertEqual(resp.context['reviews_sort_column'], resp.context['table'].columns['reviews_week'])

    def test_public_summary_ignores_duff_interval_parameters(self):
        resp = self.client.get("{0}?problems_interval=not_there&reviews_interval=neither".format(self.summary_url))
        self.assertEqual(resp.context['problems_sort_column'], resp.context['table'].columns['all_time'])
        self.assertEqual(resp.context['reviews_sort_column'], resp.context['table'].columns['reviews_all_time'])


    @override_settings(SUMMARY_THRESHOLD=None)
    def test_get_interval_counts_works_with_duplicate_names(self):
        # Issue #1167 - when two orgs had identical names, the code in
        # Summary.get_interval_counts could mix up the problem and
        # review data if the two orgs with the same name were in
        # different orders in the two sets of data
        # (Possible because the sorting can't guarantee anything when
        # sorting by the name field alone)

        # Add a new org with the same name as a previous one:
        duplicate_name_hospital = create_test_organisation({
            'ods_code': 'DUPE1',
            'organisation_type': 'hospitals',
            'parent': self.test_hospital.parent,
            'name': self.test_hospital.name
        })

        expected_organisation_data = [
            {
                'week': 0,
                'ods_code': duplicate_name_hospital.ods_code,
                'name': duplicate_name_hospital.name,
                'happy_outcome': None,
                'average_time_to_acknowledge': None,
                'reviews_week': 0,
                'six_months': 0,
                'all_time': 0,
                'four_weeks': 0,
                'reviews_all_time': 0,
                'average_recommendation_rating': None,
                'average_time_to_address': None,
                'reviews_four_weeks': 0,
                'id': duplicate_name_hospital.id,
                'reviews_six_months': 0,
                'happy_service': None,
            },
            {
                'week': 1L,
                'ods_code': self.test_hospital.ods_code,
                'name': self.test_hospital.name,
                'happy_outcome': None,
                'average_time_to_acknowledge': None,
                'reviews_week': 1L,
                'six_months': 1L,
                'all_time': 1L,
                'four_weeks': 1L,
                'reviews_all_time': 1L,
                'average_recommendation_rating': None,
                'average_time_to_address': None,
                'reviews_four_weeks': 1L,
                'id': self.test_hospital.id,
                'reviews_six_months': 1L,
                'happy_service': None,
            }
        ]

        summary_view = Summary()

        actual_organisation_data = summary_view.get_interval_counts({}, {'organisation_type':'hospitals'}, None)
        self.assertEqual(expected_organisation_data, actual_organisation_data)


class SummaryBrowserTests(SeleniumTestCase, AuthorizationTestCase):

    def setUp(self):
        super(SummaryBrowserTests, self).setUp()
        self.summary_url = reverse('org-all-summary', kwargs={'cobrand': 'choices'})
        create_test_problem({'organisation': self.test_hospital, 'category': 'staff'})
        create_test_problem({'organisation': self.test_gp_branch,
                             'publication_status': Problem.PUBLISHED,
                             'status': Problem.ABUSIVE,
                             'category': 'cleanliness'})
        create_test_review({'organisation': self.test_hospital,
                            'api_published': datetime.utcnow().replace(tzinfo=utc),
                            'api_updated': datetime.utcnow().replace(tzinfo=utc)})

    def test_other_interval_columns_hidden(self):
        self.driver.get(self.full_url(self.summary_url))
        for column in ['week', 'four_weeks', 'six_months', 'reviews_week', 'reviews_four_weeks', 'reviews_six_months']:
            cells = self.driver.find_elements_by_css_selector('td.{0}'.format(column))
            for cell in cells:
                self.assertFalse(cell.is_displayed())

    def test_querystring_param_determines_visible_column(self):
        self.driver.get(self.full_url("{0}?problems_interval=week&reviews_interval=reviews_week".format(self.summary_url)))
        for column in ['all_time', 'four_weeks', 'six_months', 'reviews_all_time', 'reviews_four_weeks', 'reviews_six_months']:
            cells = self.driver.find_elements_by_css_selector('td.{0}'.format(column))
            for cell in cells:
                self.assertFalse(cell.is_displayed())

    def test_selecting_interval_changes_visible_columns(self):
        self.driver.get(self.full_url(self.summary_url))
        # Check week is hidden first
        cells = self.driver.find_elements_by_css_selector('td.week')
        for cell in cells:
            self.assertFalse(cell.is_displayed())
        # Select a new interval
        problem_interval_select = self.driver.find_element_by_id("problems-interval-filters")
        problem_interval_select.find_element_by_css_selector("option[value=week]").click()
        # Check all other columns are hidden
        for column in ['all_time', 'four_weeks', 'six_months']:
            cells = self.driver.find_elements_by_css_selector('td.{0}'.format(column))
            for cell in cells:
                self.assertFalse(cell.is_displayed())
        # Check week is displayed
        cells = self.driver.find_elements_by_css_selector('td.week')
        for cell in cells:
            self.assertTrue(cell.is_displayed())

    def test_selecting_interval_changes_sorting_links(self):
        self.driver.get(self.full_url(self.summary_url))
        # Check old sorting link
        header_link = self.driver.find_element_by_css_selector('#problems-intervals-header a')
        self.assertEqual(header_link.get_attribute('href').split('?')[1], 'sort=all_time')
        # Select a new interval
        problem_interval_select = self.driver.find_element_by_id("problems-interval-filters")
        problem_interval_select.find_element_by_css_selector("option[value=week]").click()
        self.assertEqual(header_link.get_attribute('href').split('?')[1], 'sort=week&problems_interval=week')

    def test_selecting_currently_sorted_interval_reloads_page(self):
        # Get a url with a predefined sort
        self.driver.get(self.full_url('{0}?sort=-all_time'.format(self.summary_url)))
        # Select a new interval
        problem_interval_select = self.driver.find_element_by_id("problems-interval-filters")
        problem_interval_select.find_element_by_css_selector("option[value=week]").click()
        # Check that the page url (well, the querystring), changes
        WebDriverWait(self.driver, 3).until(
            lambda x: self.driver.current_url.split('?')[1] == "sort=-week&problems_interval=week"
        )

    def test_searching_goes_to_individual_summary(self):
        self.driver.get(self.full_url('{0}?sort=-all_time'.format(self.summary_url)))
        # Simulate searching for a provider
        self.driver.execute_script('$("#search-org-name").val("RJ01").trigger("change")')
        self.assertEquals(self.driver.current_url, self.full_url('{0}/RJ01'.format(self.summary_url)))


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
            'ods_code': 'ABC123',
            'point': Point(-0.13, 51.5)
        })
        self.faraway_gp = create_test_organisation({
            'name': 'Far GP',
            'organisation_type': 'gppractices',
            'ods_code': 'DEF456',
            'point': Point(-0.15, 51.4)
        })
        self.nearby_hospital = create_test_organisation({
            'name': 'Nearby Hospital',
            'organisation_type': 'hospitals',
            'ods_code': 'HOS123',
            'point': Point(-0.13, 51.5)
        })
        self.base_url = reverse('org-pick-provider', kwargs={'cobrand': 'choices'})
        self.results_url = "%s?location=SW1A+1AA" % self.base_url

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
        resp = self.client.get("%s?location=nearby" % self.base_url)
        self.assertContains(resp, self.nearby_gp.name, count=1, status_code=200)

    def test_results_page_does_not_show_organisation_with_other_name(self):
        resp = self.client.get("%s?location=nearby" % self.base_url)
        self.assertNotContains(resp, self.faraway_gp.name, status_code=200)

    def test_results_page_shows_paginator_for_over_ten_results(self):
        for i in range(12):
            create_test_organisation({
                'name': 'Multi GP',
                'organisation_type': 'gppractices',
                'ods_code': 'ABC{0}'.format(i)
            })
        resp = self.client.get("%s?location=multi" % self.base_url)
        self.assertContains(resp, 'Multi GP', count=10, status_code=200)
        self.assertContains(resp, 'next', count=1)

    def test_results_page_no_paginator_for_under_ten_results(self):
        for i in range(3):
            create_test_organisation({
                'name': 'Multi GP',
                'organisation_type': 'gppractices',
                'ods_code': 'DEF{0}'.format(i)
            })
        resp = self.client.get("%s?location=multi" % self.base_url)
        self.assertContains(resp, 'Multi GP', count=3, status_code=200)
        self.assertNotContains(resp, 'next')

    def test_validates_location_present(self):
        resp = self.client.get("%s?location=" % self.base_url)
        self.assertContains(resp, 'Please enter a location', count=1, status_code=200)

    def test_shows_message_on_no_results(self):
        resp = self.client.get("%s?location=non-existent" % self.base_url)
        self.assertContains(resp, "We couldn&#39;t find any matches", count=1, status_code=200)
        self.assertContains(resp, OrganisationFinderForm.PILOT_SEARCH_CAVEAT)

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
        mock_results = MagicMock()
        ordered_results = mock_results.distance().order_by('distance')
        ordered_results.return_value = []
        Organisation.objects.filter = mock_results
        resp = self.client.get(self.results_url)
        expected_message = 'Sorry, there are no matches within 5 miles of SW1A 1AA. Please try again'
        self.assertContains(resp, expected_message, count=1, status_code=200)
        self.assertContains(resp, OrganisationFinderForm.PILOT_SEARCH_CAVEAT)


class NotFoundTest(TestCase):

    def setUp(self):
        self.logger = logging.getLogger('django.request')
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.ERROR)

    def tearDown(self):
        self.logger.setLevel(self.previous_level)

    def test_page_not_found_returns_404_status(self):
        resp = self.client.get('/somthing-that-doesnt-exist')
        self.assertEquals(404, resp.status_code)


class OrganisationSearchTests(TestCase):
    def setUp(self):
        self.search_url = reverse('org-search', kwargs={'cobrand': 'choices'})

    def test_search_page_exists(self):
        resp = self.client.get(self.search_url)
        self.assertEqual(200, resp.status_code)

    def test_no_search_term_returns_no_results(self):
        resp = self.client.get(self.search_url + '?term=')
        self.assertEqual('[]', resp.content)

    def test_search_returns_organisations(self):
        org = create_test_organisation({'name': "Test Organisation"})
        resp = self.client.get(self.search_url + '?term=Tes')
        self.assertContains(resp, org.name)
