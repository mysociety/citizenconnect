# encoding: utf-8
import datetime
from decimal import Decimal

# Django imports
from django.core.urlresolvers import reverse

# App imports
from citizenconnect.browser_testing import SeleniumTestCase
from issues.models import Problem

from ..models import FriendsAndFamilySurvey

from .lib import (
    create_test_problem,
    create_test_service,
    create_test_organisation,
    AuthorizationTestCase
)


class OrganisationSummaryTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationSummaryTests, self).setUp()

        self.service = create_test_service({'organisation': self.test_hospital})

        # Problems
        atts = {'organisation': self.test_hospital}
        atts.update({'category': 'cleanliness',
                     'happy_service': True,
                     'happy_outcome': None,
                     'time_to_acknowledge': 5100,
                     'time_to_address': 54300})
        self.cleanliness_problem = create_test_problem(atts)
        atts.update({'category': 'staff',
                     'happy_service': True,
                     'happy_outcome': True,
                     'time_to_acknowledge': None,
                     'time_to_address': None})
        self.staff_problem = create_test_problem(atts)
        atts.update({'category': 'other',
                     'service_id': self.service.id,
                     'happy_service': False,
                     'happy_outcome': True,
                     'time_to_acknowledge': 7100,
                     'time_to_address': None})
        self.other_dept_problem = create_test_problem(atts)
        atts.update({'category': 'access',
                     'service_id': None,
                     'happy_service': False,
                     'happy_outcome': False,
                     'time_to_acknowledge': 2100,
                     'time_to_address': 2300,
                     'status': Problem.ABUSIVE})
        self.hidden_status_access_problem = create_test_problem(atts)

        self.public_summary_url = reverse('public-org-summary', kwargs={'ods_code': self.test_hospital.ods_code,
                                                                        'cobrand': 'choices'})
        self.private_summary_url = reverse('private-org-summary', kwargs={'ods_code': self.test_hospital.ods_code})
        self.urls = [self.public_summary_url, self.private_summary_url]

    def test_summary_page_exists(self):
        for url in self.urls:
            self.login_as(self.trust_user)
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_raises_404_not_500(self):
        # Issue #878 - views inheriting from OrganisationAwareViewMixin
        # didn't catch Organisation.DoesNotExist and raise an Http404
        # so we got a 500 instead
        missing_url = reverse('public-org-summary', kwargs={'ods_code': 'missing',
                                                            'cobrand': 'choices'})
        resp = self.client.get(missing_url)
        self.assertEqual(resp.status_code, 404)

    def test_summary_page_shows_organisation_name(self):
        for url in self.urls:
            self.login_as(self.trust_user)
            resp = self.client.get(url)
            self.assertTrue(self.test_hospital.name in resp.content)

    def test_private_summary_page_shows_all_problems(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.private_summary_url)

        problems_by_status = resp.context['problems_by_status']
        self.assertEqual(problems_by_status[0]['all_time'], 3)
        self.assertEqual(problems_by_status[0]['week'], 3)
        self.assertEqual(problems_by_status[0]['four_weeks'], 3)
        self.assertEqual(problems_by_status[0]['six_months'], 3)
        self.assertEqual(problems_by_status[0]['description'], 'Open')

        self.assertEqual(problems_by_status[1]['all_time'], 0)
        self.assertEqual(problems_by_status[1]['week'], 0)
        self.assertEqual(problems_by_status[1]['four_weeks'], 0)
        self.assertEqual(problems_by_status[1]['six_months'], 0)
        self.assertEqual(problems_by_status[1]['description'], 'In Progress')

        self.assertEqual(problems_by_status[2]['all_time'], 0)
        self.assertEqual(problems_by_status[2]['week'], 0)
        self.assertEqual(problems_by_status[2]['four_weeks'], 0)
        self.assertEqual(problems_by_status[2]['six_months'], 0)
        self.assertEqual(problems_by_status[2]['description'], 'Closed')

        self.assertEqual(problems_by_status[6]['all_time'], 1)
        self.assertEqual(problems_by_status[6]['week'], 1)
        self.assertEqual(problems_by_status[6]['four_weeks'], 1)
        self.assertEqual(problems_by_status[6]['six_months'], 1)
        self.assertEqual(problems_by_status[6]['description'], 'Abusive/Vexatious')

    def test_public_summary_page_only_shows_visible_problems(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.public_summary_url)

        problems_by_status = resp.context['problems_by_status']
        self.assertEqual(problems_by_status[0]['all_time'], 3)
        self.assertEqual(problems_by_status[0]['week'], 3)
        self.assertEqual(problems_by_status[0]['four_weeks'], 3)
        self.assertEqual(problems_by_status[0]['six_months'], 3)
        self.assertEqual(problems_by_status[0]['description'], 'Open')

        self.assertEqual(problems_by_status[1]['all_time'], 0)
        self.assertEqual(problems_by_status[1]['week'], 0)
        self.assertEqual(problems_by_status[1]['four_weeks'], 0)
        self.assertEqual(problems_by_status[1]['six_months'], 0)
        self.assertEqual(problems_by_status[1]['description'], 'In Progress')

        self.assertEqual(problems_by_status[2]['all_time'], 0)
        self.assertEqual(problems_by_status[2]['week'], 0)
        self.assertEqual(problems_by_status[2]['four_weeks'], 0)
        self.assertEqual(problems_by_status[2]['six_months'], 0)
        self.assertEqual(problems_by_status[2]['description'], 'Closed')

    def test_summary_page_applies_problem_category_filter(self):
        for url in self.urls:
            self.login_as(self.trust_user)
            resp = self.client.get(url + '?category=cleanliness')

            problems_by_status = resp.context['problems_by_status']
            self.assertEqual(problems_by_status[0]['all_time'], 1)
            self.assertEqual(problems_by_status[0]['week'], 1)
            self.assertEqual(problems_by_status[0]['four_weeks'], 1)
            self.assertEqual(problems_by_status[0]['six_months'], 1)

    def test_summary_page_applies_department_filter(self):
        for url in self.urls:
            self.login_as(self.trust_user)
            resp = self.client.get(url + '?service_id=%s' % self.service.id)

            problems_by_status = resp.context['problems_by_status']
            self.assertEqual(problems_by_status[0]['all_time'], 1)
            self.assertEqual(problems_by_status[0]['week'], 1)
            self.assertEqual(problems_by_status[0]['four_weeks'], 1)
            self.assertEqual(problems_by_status[0]['six_months'], 1)

    def test_summary_page_applies_breach_filter_on_private_pages(self):
        # Add a breach problem
        create_test_problem({'organisation': self.test_hospital,
                             'breach': True})

        self.login_as(self.trust_user)
        resp = self.client.get(self.private_summary_url + '?flags=breach')

        problems_by_status = resp.context['problems_by_status']
        self.assertEqual(problems_by_status[0]['all_time'], 1)
        self.assertEqual(problems_by_status[0]['week'], 1)
        self.assertEqual(problems_by_status[0]['four_weeks'], 1)
        self.assertEqual(problems_by_status[0]['six_months'], 1)

    def test_summary_page_applies_formal_complaint_filter_on_private_pages(self):
        create_test_problem({'organisation': self.test_hospital,
                             'formal_complaint': True})

        self.login_as(self.trust_user)
        resp = self.client.get(self.private_summary_url + '?flags=formal_complaint')

        problems_by_status = resp.context['problems_by_status']
        self.assertEqual(problems_by_status[0]['all_time'], 1)
        self.assertEqual(problems_by_status[0]['week'], 1)
        self.assertEqual(problems_by_status[0]['four_weeks'], 1)
        self.assertEqual(problems_by_status[0]['six_months'], 1)

    def test_public_summary_page_does_not_have_breach_filter(self):
        resp = self.client.get(self.public_summary_url)
        self.assertNotContains(resp, '<option value="breach">')

    def test_public_summary_page_does_not_have_formal_complaint_filter(self):
        resp = self.client.get(self.public_summary_url)
        self.assertNotContains(resp, '<option value="formal_complaint">')

    def test_summary_page_gets_survey_data_for_problems_in_visible_statuses(self):
        for url in self.urls:
            self.login_as(self.trust_user)
            resp = self.client.get(url)
            issues_total = resp.context['issues_total']
            self.assertEqual(issues_total['happy_service'], 0.666666666666667)
            self.assertEqual(issues_total['happy_outcome'], 1.0)

    def test_summary_page_gets_time_limit_data_for_problems_in_visible_statuses(self):
        for url in self.urls:
            self.login_as(self.trust_user)
            resp = self.client.get(url)
            issues_total = resp.context['issues_total']
            self.assertEqual(issues_total['average_time_to_acknowledge'], Decimal('6100.0000000000000000'))
            self.assertEqual(issues_total['average_time_to_address'], Decimal('54300.0000000000000000000'))

    def test_public_summary_page_shows_only_visible_status_rows(self):
        resp = self.client.get(self.public_summary_url)

        for status in Problem.VISIBLE_STATUSES:
            self.assertContains(resp, Problem.STATUS_CHOICES[status][1])

        for status in Problem.HIDDEN_STATUSES:
            self.assertNotContains(resp, Problem.STATUS_CHOICES[status][1])

    def test_private_summary_page_shows_visible_and_hidden_status_rows(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.private_summary_url)
        self.assertContains(resp, 'Closed', count=1, status_code=200)
        self.assertContains(resp, 'Unable to Resolve', count=1)
        self.assertContains(resp, 'Abusive/Vexatious', count=1)

    def test_summary_page_does_not_include_problems_in_hidden_statuses_in_total_row_summary_stats(self):
        for url in self.urls:
            self.login_as(self.trust_user)
            resp = self.client.get(url)
            summary_stats = resp.context['problems_summary_stats']
            self.assertEqual(summary_stats['happy_service'], 0.666666666666667)
            self.assertEqual(summary_stats['happy_outcome'], 1.0)
            self.assertEqual(summary_stats['average_time_to_acknowledge'], Decimal('6100.0000000000000000'))
            self.assertEqual(summary_stats['average_time_to_address'], Decimal('54300.0000000000000000000'))

    def test_summary_pages_display_summary_stats_values_in_visible_status_rows(self):
        for url in self.urls:
            self.login_as(self.trust_user)
            resp = self.client.get(url)
            self.assertContains(resp, '<td class="average_time_to_acknowledge" id="status_0_time_to_acknowledge">4 days</td>')
            self.assertContains(resp, '<td class="average_time_to_address" id="status_0_time_to_address">38 days</td>')
            self.assertContains(resp, '<td class="happy_service" id="status_0_happy_service">67%</td>')
            self.assertContains(resp, '<td class="happy_outcome" id="status_0_happy_outcome">100%</td>')

    def test_private_summary_page_does_not_display_summary_stats_values_in_hidden_status_rows(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.private_summary_url)
        self.assertContains(resp, '<td class="average_time_to_acknowledge" id="status_6_time_to_acknowledge">—</td>')
        self.assertContains(resp, '<td class="average_time_to_address" id="status_6_time_to_address">—</td>')
        self.assertContains(resp, '<td class="happy_service" id="status_6_happy_service">—</td>')
        self.assertContains(resp, '<td class="happy_outcome" id="status_6_happy_outcome">—</td>')

    def test_public_summary_page_is_accessible_to_everyone(self):
        resp = self.client.get(self.public_summary_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_summary_page_is_inaccessible_to_anon_users(self):
        expected_login_url = "{0}?next={1}".format(self.login_url, self.private_summary_url)
        resp = self.client.get(self.private_summary_url)
        self.assertRedirects(resp, expected_login_url)

    def test_private_summary_page_is_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.private_summary_url)
            self.assertEqual(resp.status_code, 200)

    def test_private_summary_page_is_accessible_to_ccg(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.private_summary_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_summary_page_is_inaccessible_to_other_trusts(self):
        self.login_as(self.gp_surgery_user)
        resp = self.client.get(self.private_summary_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_summary_page_is_inaccessible_to_other_ccgs(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.private_summary_url)
        self.assertEqual(resp.status_code, 403)


class OrganisationTabsTests(AuthorizationTestCase):
    """Test that the tabs shown on organisation pages link to the right places"""

    def setUp(self):
        super(OrganisationTabsTests, self).setUp()
        self.summary_url = reverse('public-org-summary', kwargs={'ods_code': self.test_hospital.ods_code, 'cobrand': 'choices'})
        self.problems_url = reverse('public-org-problems', kwargs={'ods_code': self.test_hospital.ods_code, 'cobrand': 'choices'})
        self.reviews_url = reverse('public-org-reviews', kwargs={'ods_code': self.test_hospital.ods_code, 'cobrand': 'choices'})
        self.surveys_url = reverse('public-org-surveys', kwargs={'ods_code': self.test_hospital.ods_code, 'cobrand': 'choices'})
        self.tab_urls = [
            self.reviews_url,
            self.problems_url,
            self.summary_url,
            self.surveys_url
        ]
        self.login_as(self.trust_user)

    def _check_tabs(self, page_url, resp):
        for url in self.tab_urls:
            self.assertContains(resp, url, msg_prefix="Response for {0} does not contain url: {1}".format(page_url, url))

    def test_tabs(self):
        self.client.logout()
        # Anon users should see these links
        for url in self.tab_urls:
                resp = self.client.get(url)
                self._check_tabs(url, resp)
        # Logged in users should see the same links
        for user in [self.nhs_superuser, self.ccg_user, self.trust_user, self.gp_surgery_user, self.other_ccg_user]:
            self.login_as(user)
            for url in self.tab_urls:
                resp = self.client.get(url)
                self._check_tabs(url, resp)


class OrganisationSurveysTests(AuthorizationTestCase):
    """Test that surveys show properly for an organisation"""

    def setUp(self):
        super(OrganisationSurveysTests, self).setUp()
        self.survey_url = reverse('public-org-surveys', kwargs={'ods_code': self.test_hospital.ods_code, 'cobrand': 'choices'})

    def test_survey_page_exists(self):
        resp = self.client.get(self.survey_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Test Organisation Friends and Family Test")
        self.assertContains(resp, "There are no surveys for Inpatient at Test Organisation at this time.")

    def assert_contains_response_value(self, response, value):
        """Helper method to check a response value is in an HttpResponse"""
        response_html = '<div class="survey__response__value  g  one-eighth  portable-one-quarter">{0}</div>'.format(value)
        self.assertContains(response, response_html)

    def assert_contains_overall_value(self, response, value, date):
        """Helper method to check an overall score is in an HttpResponse"""
        month = date.strftime("%B")
        month_year = date.strftime("%B, %Y")
        overall_html = '<li class="survey__previous__overall" data-month="{0}" data-value="{1}">{2}: {1}</li>'.format(month, value, month_year)
        self.assertContains(response, overall_html)

    def test_survey_page_shows_surveys(self):
        # Add a survey for test_hospital
        survey = FriendsAndFamilySurvey.objects.create(
            content_object=self.test_hospital,
            location='inpatient',
            overall_score=75,
            extremely_likely=10,
            likely=10,
            neither=1,
            unlikely=0,
            extremely_unlikely=1,
            dont_know=0,
            date=datetime.date(2013, 1, 1)
        )
        resp = self.client.get(self.survey_url)
        self.assertContains(resp, 'Inpatient')
        self.assert_contains_response_value(resp, survey.extremely_likely)
        self.assert_contains_response_value(resp, survey.likely)
        self.assert_contains_response_value(resp, survey.neither)
        self.assert_contains_response_value(resp, survey.unlikely)
        self.assert_contains_response_value(resp, survey.extremely_unlikely)
        self.assert_contains_response_value(resp, survey.dont_know)
        self.assertContains(resp, '<span>{0}</span>'.format(survey.overall_score))
        self.assertContains(resp, '<h3>{0}</h3>'.format(survey.date.strftime('%B, %Y')))
        self.assertContains(resp, '<h3>Previous month\'s test scores</h3>')
        self.assert_contains_overall_value(resp, survey.overall_score, survey.date)

        # Now add some more surveys
        extra_surveys = []
        for month in [2,3,4,5,6,7]:
            extra_surveys.append(FriendsAndFamilySurvey.objects.create(
                content_object=self.test_hospital,
                location='inpatient',
                overall_score=75,
                extremely_likely=10,
                likely=10,
                neither=1,
                unlikely=0,
                extremely_unlikely=1,
                dont_know=0,
                date=datetime.date(2013, month, 1)
            ))
        resp = self.client.get(self.survey_url)
        # The most recent one won't be on here, as it'll be the main one now
        self.assert_contains_overall_value(resp, 75, extra_surveys[1].date)
        self.assert_contains_overall_value(resp, 75, extra_surveys[2].date)
        self.assert_contains_overall_value(resp, 75, extra_surveys[3].date)
        self.assert_contains_overall_value(resp, 75, extra_surveys[4].date)
        self.assert_contains_overall_value(resp, 75, extra_surveys[5].date)
        # We only show the most recent 6 months, so now the first one we added
        # shouldn't be in the list either
        self.assertNotContains(resp, '{0}'.format(survey.date.strftime('%B, %Y')))


    def test_survey_page_allows_location_selection(self):
        # Add a survey for test_hospital
        survey = FriendsAndFamilySurvey.objects.create(
            content_object=self.test_hospital,
            location='aande',
            overall_score=75,
            extremely_likely=10,
            likely=10,
            neither=1,
            unlikely=0,
            extremely_unlikely=1,
            dont_know=0,
            date=datetime.date(2013, 1, 1)
        )
        # Choose the A&E location
        resp = self.client.get("{0}?location=aande".format(self.survey_url))
        self.assertContains(resp, 'A&amp;E')
        self.assert_contains_response_value(resp, survey.extremely_likely)
        self.assert_contains_response_value(resp, survey.likely)
        self.assert_contains_response_value(resp, survey.neither)
        self.assert_contains_response_value(resp, survey.unlikely)
        self.assert_contains_response_value(resp, survey.extremely_unlikely)
        self.assert_contains_response_value(resp, survey.dont_know)
        self.assertContains(resp, '<span>{0}</span>'.format(survey.overall_score))
        self.assertContains(resp, '<h3>{0}</h3>'.format(survey.date.strftime('%B, %Y')))
        self.assertContains(resp, '<h3>Previous month\'s test scores</h3>')
        self.assert_contains_overall_value(resp, survey.overall_score, survey.date)


class OrganisationSurveysBrowserTests(SeleniumTestCase):

    def setUp(self):
        super(OrganisationSurveysBrowserTests, self).setUp()
        self.test_organisation = create_test_organisation({})
        self.surveys = []
        for month in [1,2,3,4,5]:
            self.surveys.append(FriendsAndFamilySurvey.objects.create(
                content_object=self.test_organisation,
                location='inpatient',
                overall_score=75,
                extremely_likely=10,
                likely=10,
                neither=1,
                unlikely=0,
                extremely_unlikely=1,
                dont_know=0,
                date=datetime.date(2013, month, 1)
            ))
        self.surveys_url = reverse('public-org-surveys', kwargs={'ods_code': self.test_organisation.ods_code, 'cobrand': 'choices'})

    def test_graph_is_drawn(self):
        self.driver.get(self.full_url(self.surveys_url))
        graph_container = self.driver.find_element_by_css_selector('.survey__previous')
        # Check the canvas is there and showing
        canvas = graph_container.find_element_by_css_selector('canvas.flot-base')
        self.assertTrue(canvas.is_displayed())
        # Check the right months have been put into the graph
        labels = graph_container.find_elements_by_css_selector('.flot-x-axis .flot-tick-label')
        for index, survey in enumerate(self.surveys):
            month_name = survey.date.strftime("%B")
            self.assertEqual(labels[index].text, month_name)
