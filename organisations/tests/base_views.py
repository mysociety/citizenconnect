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
from . import (create_test_problem,
               create_test_organisation,
               create_test_service,
               create_test_review,
               AuthorizationTestCase)
from organisations.forms import OrganisationFinderForm


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


@override_settings(SUMMARY_THRESHOLD=None)
class PrivateNationalSummaryTests(AuthorizationTestCase):

    def setUp(self):
        super(PrivateNationalSummaryTests, self).setUp()
        self.summary_url = reverse('private-national-summary')
        create_test_problem({'organisation': self.test_hospital})
        create_test_problem({'organisation': self.test_gp_branch,
                             'publication_status': Problem.PUBLISHED,
                             'status': Problem.ABUSIVE})
        self.login_as(self.superuser)

    def test_summary_page_authorization(self):

        tests = (
            # (user, permitted? )
            (None,                               False),
            (self.trust_user,                    False),
            (self.case_handler,                  False),
            (self.second_tier_moderator,         False),
            (self.ccg_user,                      False),
            (self.no_ccg_user,                   False),

            (self.superuser,                     True),
            (self.nhs_superuser,                 True),
            (self.customer_contact_centre_user,  True),
        )

        for user, permitted in tests:
            self.client.logout()
            if user:
                self.login_as(user)
            resp = self.client.get(self.summary_url)

            if permitted:
                self.assertEqual(resp.status_code, 200, "{0} should be allowed".format(user))
            elif user:  # trying to access and logged in
                self.assertEqual(resp.status_code, 403, "{0} should be denied".format(user))
            else:  # trying to access and not logged in
                expected_redirect_url = "{0}?next={1}".format(reverse("login"), self.summary_url)
                self.assertRedirects(resp, expected_redirect_url, msg_prefix="{0} should not be allowed".format(user))

    def test_summary_page_exists(self):
        resp = self.client.get(self.summary_url)
        self.assertEqual(resp.status_code, 200)

    def test_summary_shows_all_statuses_for_problems_in_filters(self):
        resp = self.client.get(self.summary_url)
        for status_enum, status_name in Problem.STATUS_CHOICES:
            self.assertContains(resp, '<option value="{0}">{1}</option>'.format(status_enum, status_name))

    def test_filters_by_ccg(self):
        # Check see both ccgs
        resp = self.client.get(self.summary_url)
        for org_parent in self.test_ccg.organisation_parents.all():
            for org in org_parent.organisations.all():
                self.assertContains(resp, org.name)
        for org_parent in self.other_test_ccg.organisation_parents.all():
            for org in org_parent.organisations.all():
                self.assertContains(resp, org.name)

        # Apply CCG filter
        resp = self.client.get("{0}?ccg={1}".format(self.summary_url, self.test_ccg.id))

        # Check filter applied
        for org_parent in self.test_ccg.organisation_parents.all():
            for org in org_parent.organisations.all():
                self.assertContains(resp, org.name)
        for org_parent in self.other_test_ccg.organisation_parents.all():
            for org in org_parent.organisations.all():
                self.assertNotContains(resp, org.name)

    def test_summary_page_applies_threshold_from_settings(self):
        with self.settings(SUMMARY_THRESHOLD=('six_months', 1)):
            resp = self.client.get(self.summary_url)
            self.assertContains(resp, 'Test Organisation')

        with self.settings(SUMMARY_THRESHOLD=('six_months', 2)):
            resp = self.client.get(self.summary_url)
            self.assertNotContains(resp, 'Test Organisation')

    def test_summary_page_filters_by_breach(self):
        # Add a breach problem
        create_test_problem({'organisation': self.test_hospital,
                             'breach': True})

        breach_filtered_url = '{0}?flags=breach'.format(self.summary_url)
        resp = self.client.get(breach_filtered_url)
        other_test_org_record = resp.context['table'].rows[0].record
        test_org_record = resp.context['table'].rows[1].record
        self.assertEqual(test_org_record['week'], 1)
        self.assertEqual(other_test_org_record['week'], 0)

    def test_summary_page_filters_by_formal_complaint(self):
        # Add a formal_complaint problem
        create_test_problem({'organisation': self.test_hospital,
                             'formal_complaint': True})

        formal_complaint_filtered_url = '{0}?flags=formal_complaint'.format(self.summary_url)
        resp = self.client.get(formal_complaint_filtered_url)
        other_test_org_record = resp.context['table'].rows[0].record
        test_org_record = resp.context['table'].rows[1].record
        self.assertEqual(test_org_record['week'], 1)
        self.assertEqual(other_test_org_record['week'], 0)


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


class EscalationDashboardTests(AuthorizationTestCase):

    def setUp(self):
        super(EscalationDashboardTests, self).setUp()
        self.escalation_dashboard_url = reverse('escalation-dashboard')
        self.org_local_escalated_problem = create_test_problem({'organisation': self.test_hospital,
                                                                'status': Problem.ESCALATED,
                                                                'commissioned': Problem.LOCALLY_COMMISSIONED})
        self.org_national_escalated_problem = create_test_problem({'organisation': self.test_hospital,
                                                                   'status': Problem.ESCALATED,
                                                                   'commissioned': Problem.NATIONALLY_COMMISSIONED})
        self.other_org_local_escalated_problem = create_test_problem({'organisation': self.test_gp_branch,
                                                                      'status': Problem.ESCALATED,
                                                                      'commissioned': Problem.LOCALLY_COMMISSIONED})
        self.other_org_national_escalated_problem = create_test_problem({'organisation': self.test_gp_branch,
                                                                         'status': Problem.ESCALATED,
                                                                         'commissioned': Problem.NATIONALLY_COMMISSIONED})

        self.org_local_escalated_acknowledged_problem = create_test_problem({'organisation': self.test_hospital,
                                                                             'status': Problem.ESCALATED_ACKNOWLEDGED,
                                                                             'commissioned': Problem.LOCALLY_COMMISSIONED})
        self.org_local_escalated_resolved_problem = create_test_problem({'organisation': self.test_hospital,
                                                                         'status': Problem.ESCALATED_RESOLVED,
                                                                         'commissioned': Problem.LOCALLY_COMMISSIONED})
        # Add two services to the test org
        self.service_one = create_test_service({'organisation': self.test_hospital})
        self.service_two = create_test_service({'organisation': self.test_hospital,
                                                'name': 'service two',
                                                'service_code': 'SRV222'})
        self.test_hospital.services.add(self.service_one)
        self.test_hospital.services.add(self.service_two)
        self.test_hospital.save()

    def test_dashboard_accessible_to_customer_contact_centre(self):
        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.escalation_dashboard_url)
            self.assertEqual(resp.status_code, 200)

    def test_dashboard_is_inacessible_to_anyone_else(self):
        people_who_shouldnt_have_access = [
            self.trust_user,
            self.no_trust_user,
            self.gp_surgery_user,
            self.second_tier_moderator,
            self.ccg_user,
            self.other_ccg_user,
            self.no_ccg_user
        ]

        for user in people_who_shouldnt_have_access:
            self.login_as(user)
            resp = self.client.get(self.escalation_dashboard_url)
            self.assertEqual(resp.status_code, 403, '{0} can access {1} when they shouldn\'t be able to'.format(user.username, self.escalation_dashboard_url))

    def test_dashboard_doesnt_show_escalated_resolved_problem(self):
        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertNotContains(resp, self.org_local_escalated_resolved_problem.reference_number)

    def test_dashboard_only_shows_nationally_commissioned_problems_to_customer_care_centre(self):
        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.escalation_dashboard_url)
        # Shows nationally commissioned problems for all orgs
        self.assertContains(resp, self.org_national_escalated_problem.reference_number)
        self.assertContains(resp, self.other_org_national_escalated_problem.reference_number)
        # Does not show locally commissioned problems
        self.assertNotContains(resp, self.org_local_escalated_problem.reference_number)
        self.assertNotContains(resp, self.other_org_local_escalated_problem.reference_number)

    def test_dashboard_shows_all_problems_to_superuser(self):
        self.login_as(self.nhs_superuser)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, self.org_local_escalated_problem.reference_number)
        self.assertContains(resp, self.org_national_escalated_problem.reference_number)
        self.assertContains(resp, self.org_local_escalated_acknowledged_problem.reference_number)
        self.assertContains(resp, self.other_org_local_escalated_problem.reference_number)
        self.assertContains(resp, self.other_org_national_escalated_problem.reference_number)

    def test_dashboard_has_ccg_filter(self):
        ccg_filter_to_look_for = 'name="ccg"'

        self.login_as(self.nhs_superuser)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, ccg_filter_to_look_for)

        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, ccg_filter_to_look_for)

    def test_dashboard_hides_status_filter(self):
        status_filter_to_look_for = 'name="status"'

        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertNotContains(resp, status_filter_to_look_for)

    def test_filters_by_ccg(self):
        # Have to login as a superuser to see the ccg filter
        self.login_as(self.nhs_superuser)
        ccg_filtered_url = '{0}?ccg={1}'.format(self.escalation_dashboard_url, self.test_ccg.id)
        resp = self.client.get(ccg_filtered_url)
        self.assertContains(resp, self.org_local_escalated_problem.reference_number)
        # Because we're the superuser, we should see this too
        self.assertContains(resp, self.org_national_escalated_problem.reference_number)
        # These are both associated with the other ccg
        self.assertNotContains(resp, self.other_org_local_escalated_problem.reference_number)
        self.assertNotContains(resp, self.other_org_national_escalated_problem.reference_number)

    def test_filters_by_provider_type(self):
        # self.test_hospital is a hospital, self.test_other_organisation is a GP
        # Need to login as superuser to be able to see both problems anyway
        self.login_as(self.nhs_superuser)
        problem_filtered_url = '{0}?organisation_type=hospitals'.format(self.escalation_dashboard_url)
        resp = self.client.get(problem_filtered_url)
        self.assertContains(resp, self.org_local_escalated_problem.reference_number)
        self.assertContains(resp, self.org_national_escalated_problem.reference_number)
        # These are both associated with a Hospital
        self.assertNotContains(resp, self.other_org_local_escalated_problem.reference_number)
        self.assertNotContains(resp, self.other_org_national_escalated_problem.reference_number)

    def test_filters_by_department(self):
        # Add some problems to the test org against specific services
        service_one_problem = create_test_problem({'organisation': self.test_hospital,
                                                   'service': self.service_one,
                                                   'status': Problem.ESCALATED,
                                                   'commissioned': Problem.NATIONALLY_COMMISSIONED})
        service_two_problem = create_test_problem({'organisation': self.test_hospital,
                                                   'service': self.service_two,
                                                   'status': Problem.ESCALATED,
                                                   'commissioned': Problem.NATIONALLY_COMMISSIONED})
        department_filtered_url = '{0}?service_code={1}'.format(self.escalation_dashboard_url, self.service_one.service_code)

        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(department_filtered_url)

        self.assertContains(resp, service_one_problem.reference_number)
        self.assertNotContains(resp, service_two_problem.reference_number)
        # This doesn't have a service, so we shouldn't see it either
        self.assertNotContains(resp, self.org_local_escalated_problem.reference_number)

    def test_filters_by_problem_category(self):
        cleanliness_problem = create_test_problem({'organisation': self.test_hospital,
                                                   'service': self.service_one,
                                                   'status': Problem.ESCALATED,
                                                   'commissioned': Problem.NATIONALLY_COMMISSIONED,
                                                   'category': 'cleanliness'})
        delays_problem = create_test_problem({'organisation': self.test_hospital,
                                              'service': self.service_two,
                                              'status': Problem.ESCALATED,
                                              'commissioned': Problem.NATIONALLY_COMMISSIONED,
                                              'category': 'delays'})
        category_filtered_url = '{0}?category=delays'.format(self.escalation_dashboard_url)

        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(category_filtered_url)

        self.assertContains(resp, delays_problem.reference_number)
        self.assertNotContains(resp, cleanliness_problem.reference_number)
        # This is in "staff" so shouldn't show either
        self.assertNotContains(resp, self.org_local_escalated_problem.reference_number)

    def test_filters_by_breach(self):
        breach_problem = create_test_problem({'organisation': self.test_hospital,
                                              'service': self.service_two,
                                              'status': Problem.ESCALATED,
                                              'commissioned': Problem.NATIONALLY_COMMISSIONED,
                                              'breach': True})
        breach_filtered_url = '{0}?flags=breach'.format(self.escalation_dashboard_url)

        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(breach_filtered_url)

        self.assertContains(resp, breach_problem.reference_number)
        # This is not a breach, so shouldn't show
        self.assertNotContains(resp, self.org_local_escalated_problem.reference_number)

    def test_dashboard_shows_breach_flag(self):
        # Add a breach problem that should show up
        create_test_problem({'organisation': self.test_hospital,
                             'service': self.service_two,
                             'status': Problem.ESCALATED,
                             'commissioned': Problem.NATIONALLY_COMMISSIONED,
                             'breach': True})
        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, '<div class="problem-table__flag__breach">b</div>')

    def test_dashboard_shows_escalation_flag(self):
        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, '<div class="problem-table__flag__escalate">e</div>')

    def test_dashboard_highlights_priority_problems(self):
        self.login_as(self.customer_contact_centre_user)
        # Up the priority of a problem
        self.org_national_escalated_problem.priority = Problem.PRIORITY_HIGH
        self.org_national_escalated_problem.save()
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, 'problem-table__highlight')


class BreachDashboardTests(AuthorizationTestCase):

    def setUp(self):
        super(BreachDashboardTests, self).setUp()
        self.breach_dashboard_url = reverse('escalation-breaches')
        self.org_breach_problem = create_test_problem({'organisation': self.test_hospital,
                                                       'breach': True})
        self.other_org_breach_problem = create_test_problem({'organisation': self.test_gp_branch,
                                                             'breach': True})
        self.org_problem = create_test_problem({'organisation': self.test_hospital})

    def test_dashboard_accessible_to_customer_contact_centre(self):
        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.breach_dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.breach_dashboard_url)
            self.assertEqual(resp.status_code, 200)

    def test_dashboard_is_inacessible_to_anyone_else(self):
        people_who_shouldnt_have_access = [
            self.trust_user,
            self.no_trust_user,
            self.gp_surgery_user,
            self.second_tier_moderator,
            self.ccg_user,
            self.other_ccg_user,
            self.no_ccg_user
        ]

        for user in people_who_shouldnt_have_access:
            self.login_as(user)
            resp = self.client.get(self.breach_dashboard_url)
            self.assertEqual(resp.status_code, 403, '{0} can access {1} when they shouldn\'t be able to'.format(user.username, self.breach_dashboard_url))

    def test_dashboard_only_shows_breach_problems(self):
        for user in (self.customer_contact_centre_user, self.nhs_superuser):
            self.login_as(user)
            resp = self.client.get(self.breach_dashboard_url)
            self.assertContains(resp, self.org_breach_problem.reference_number)
            self.assertNotContains(resp, self.org_problem.reference_number)

    def test_dashboard_shows_all_breaches(self):
        for user in (self.customer_contact_centre_user, self.nhs_superuser):
            self.login_as(user)
            resp = self.client.get(self.breach_dashboard_url)
            self.assertContains(resp, self.org_breach_problem.reference_number)
            self.assertContains(resp, self.other_org_breach_problem.reference_number)

    def test_dashboard_shows_breach_flag(self):
        for user in (self.customer_contact_centre_user, self.nhs_superuser):
            self.login_as(user)
            resp = self.client.get(self.breach_dashboard_url)
            self.assertContains(resp, '<div class="problem-table__flag__breach">b</div>')

    def test_dashboard_shows_escalation_flag(self):
        # Make the breach problem escalated too
        self.org_breach_problem.status = Problem.ESCALATED
        self.org_breach_problem.commissioned = Problem.LOCALLY_COMMISSIONED
        self.org_breach_problem.save()
        for user in (self.customer_contact_centre_user, self.nhs_superuser):
            self.login_as(user)
            resp = self.client.get(self.breach_dashboard_url)
            self.assertContains(resp, '<div class="problem-table__flag__escalate">e</div>')

    def test_dashboard_highlights_priority_problems(self):
        # Up the priority of the breach problem
        self.org_breach_problem.priority = Problem.PRIORITY_HIGH
        self.org_breach_problem.save()

        for user in (self.customer_contact_centre_user, self.nhs_superuser):
            self.login_as(user)
            resp = self.client.get(self.breach_dashboard_url)
            self.assertContains(resp, 'problem-table__highlight')


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
