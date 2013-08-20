# encoding: utf-8
from decimal import Decimal

# Django imports
from django.core.urlresolvers import reverse

# App imports
from issues.models import Problem

from . import (create_test_problem,
               create_test_organisation,
               create_test_service,
               create_test_organisation_parent,
               AuthorizationTestCase)


class OrganisationParentSummaryTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationParentSummaryTests, self).setUp()

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

        self.trust_summary_url = reverse('org-parent-summary', kwargs={'code': self.test_hospital.parent.code})

    def test_summary_page_exists(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url)
        self.assertEqual(resp.status_code, 200)

    def test_raises_404_not_500(self):
        # Issue #878 - views inheriting from OrganisationParentAwareViewMixin
        # didn't catch OrganisationParent.DoesNotExist and raise an Http404
        # so we got a 500 instead
        missing_url = reverse('org-parent-summary', kwargs={'code': 'missing'})
        self.login_as(self.nhs_superuser)  # Superuser to avoid being redirected to login first
        resp = self.client.get(missing_url)
        self.assertEqual(resp.status_code, 404)

    def test_summary_page_shows_trust_name(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url)
        self.assertTrue(self.test_hospital.parent.name in resp.content)

    def test_summary_page_applies_problem_category_filter(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url + '?category=cleanliness')

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
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url + '?service_id=%s' % self.service.id)

        problems_by_status = resp.context['problems_by_status']
        self.assertEqual(problems_by_status[0]['all_time'], 3L)
        self.assertEqual(problems_by_status[0]['week'], 3L)
        self.assertEqual(problems_by_status[0]['four_weeks'], 3L)
        self.assertEqual(problems_by_status[0]['six_months'], 3L)

    def test_summary_page_applies_breach_filter_on_private_pages(self):
        # Add a breach problem
        create_test_problem({'organisation': self.test_hospital,
                             'breach': True})

        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url + '?flags=breach')

        problems_by_status = resp.context['problems_by_status']
        self.assertEqual(problems_by_status[0]['all_time'], 1)
        self.assertEqual(problems_by_status[0]['week'], 1)
        self.assertEqual(problems_by_status[0]['four_weeks'], 1)
        self.assertEqual(problems_by_status[0]['six_months'], 1)

    def test_summary_page_applies_formal_complaint_filter_on_private_pages(self):
        # Add a formal_complaint problem
        create_test_problem({'organisation': self.test_hospital,
                             'formal_complaint': True})

        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url + '?flags=formal_complaint')

        problems_by_status = resp.context['problems_by_status']
        self.assertEqual(problems_by_status[0]['all_time'], 1)
        self.assertEqual(problems_by_status[0]['week'], 1)
        self.assertEqual(problems_by_status[0]['four_weeks'], 1)
        self.assertEqual(problems_by_status[0]['six_months'], 1)

    def test_summary_page_gets_survey_data_for_problems_in_visible_statuses(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url)
        issues_total = resp.context['issues_total']
        self.assertEqual(issues_total['happy_service'], 0.666666666666667)
        self.assertEqual(issues_total['happy_outcome'], 1.0)

    def test_summary_page_gets_time_limit_data_for_problems_in_visible_statuses(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url)
        issues_total = resp.context['issues_total']
        self.assertEqual(issues_total['average_time_to_acknowledge'], Decimal('6100.0000000000000000'))
        self.assertEqual(issues_total['average_time_to_address'], Decimal('54300.0000000000000000000'))

    def test_private_summary_page_shows_all_problems(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url)
        total = resp.context['problems_total']
        self.assertEqual(total['all_time'], 4)
        self.assertEqual(total['week'], 4)
        self.assertEqual(total['four_weeks'], 4)
        self.assertEqual(total['six_months'], 4)

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

    def test_private_summary_page_shows_visible_and_hidden_status_rows(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url)
        self.assertContains(resp, 'Closed', count=1, status_code=200)
        self.assertContains(resp, 'Unable to Resolve', count=1)
        self.assertContains(resp, 'Abusive/Vexatious', count=1)

    def test_summary_page_does_not_include_problems_in_hidden_statuses_in_total_row_summary_stats(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url)
        summary_stats = resp.context['problems_summary_stats']
        self.assertEqual(summary_stats['happy_service'], 0.666666666666667)
        self.assertEqual(summary_stats['happy_outcome'], 1.0)
        self.assertEqual(summary_stats['average_time_to_acknowledge'], Decimal('6100.0000000000000000'))
        self.assertEqual(summary_stats['average_time_to_address'], Decimal('54300.0000000000000000000'))

    def test_summary_pages_display_summary_stats_values_in_visible_status_rows(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url)
        self.assertContains(resp, '<td class="average_time_to_acknowledge" id="status_0_time_to_acknowledge">4 days</td>')
        self.assertContains(resp, '<td class="average_time_to_address" id="status_0_time_to_address">38 days</td>')
        self.assertContains(resp, '<td class="happy_service" id="status_0_happy_service">67%</td>')
        self.assertContains(resp, '<td class="happy_outcome" id="status_0_happy_outcome">100%</td>')

    def test_private_summary_page_does_not_display_summary_stats_values_in_hidden_status_rows(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url)
        self.assertContains(resp, '<td class="average_time_to_acknowledge" id="status_6_time_to_acknowledge">—</td>')
        self.assertContains(resp, '<td class="average_time_to_address" id="status_6_time_to_address">—</td>')
        self.assertContains(resp, '<td class="happy_service" id="status_6_happy_service">—</td>')
        self.assertContains(resp, '<td class="happy_outcome" id="status_6_happy_outcome">—</td>')

    def test_private_summary_page_is_inaccessible_to_anon_users(self):
        expected_login_url = "{0}?next={1}".format(self.login_url, self.trust_summary_url)
        resp = self.client.get(self.trust_summary_url)
        self.assertRedirects(resp, expected_login_url)

    def test_private_summary_page_is_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.trust_summary_url)
            self.assertEqual(resp.status_code, 200)

    def test_private_summary_page_is_accessible_to_ccg(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.trust_summary_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_summary_page_is_inaccessible_to_other_providers(self):
        self.login_as(self.gp_surgery_user)
        resp = self.client.get(self.trust_summary_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_summary_page_is_inaccessible_to_other_ccgs(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.trust_summary_url)
        self.assertEqual(resp.status_code, 403)

    def test_summary_page_doesnt_error_when_org_parent_has_no_orgs(self):
        # Bug #897 - when an org parent had no orgs, this view caused an
        # SQL error in interval_counts by sending it an empty list of
        # organisation_ids to filter by, it should have checked first
        # and not bothered trying to get any counts
        trust_with_no_orgs = create_test_organisation_parent(
            {
                'name': 'Trust with no orgs',
                'code': 'hagq123',
                'choices_id': 98086,
                'primary_ccg': self.test_ccg  # So that we can use the ccg user to login
            }
        )
        trust_with_no_orgs_summary_url = reverse('org-parent-summary', kwargs={'code': trust_with_no_orgs.code})
        self.login_as(self.ccg_user)
        # This would error before we fixed the bug, failing the test
        resp = self.client.get(trust_with_no_orgs_summary_url)
        self.assertEqual(resp.status_code, 200)


class OrganisationParentDashboardTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationParentDashboardTests, self).setUp()
        self.problem = create_test_problem({'organisation': self.test_hospital})
        self.dashboard_url = reverse('org-parent-dashboard', kwargs={'code': self.test_hospital.parent.code})

    def test_dashboard_page_exists(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_page_shows_trust_name(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(self.test_hospital.parent.name in resp.content)

    def test_dashboard_shows_problems(self):
        self.login_as(self.trust_user)
        response_url = reverse('response-form', kwargs={'pk': self.problem.id})
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(response_url in resp.content)

    def test_dashboard_doesnt_show_closed_problems(self):
        self.closed_problem = create_test_problem({'organisation': self.test_hospital,
                                                   'status': Problem.RESOLVED})
        closed_problem_response_url = reverse('response-form', kwargs={'pk': self.closed_problem.id})
        self.login_as(self.trust_user)
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(closed_problem_response_url not in resp.content)

    def test_dashboard_page_is_inaccessible_to_anon_users(self):
        expected_login_url = "{0}?next={1}".format(self.login_url, self.dashboard_url)
        resp = self.client.get(self.dashboard_url)
        self.assertRedirects(resp, expected_login_url)

    def test_dashboard_page_is_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.dashboard_url)
            self.assertEqual(resp.status_code, 200)

    def test_dashboard_page_is_inaccessible_to_other_trusts(self):
        self.login_as(self.gp_surgery_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 403)

    def test_dashboard_page_is_inaccessible_to_other_ccgs(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 403)

    def test_dashboard_page_highlights_priority_problems(self):
        # Add a priority problem
        self.login_as(self.trust_user)
        create_test_problem({'organisation': self.test_hospital,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'priority': Problem.PRIORITY_HIGH})
        resp = self.client.get(self.dashboard_url)
        self.assertContains(resp, 'problem-table__highlight')

    def test_dashboard_page_shows_breach_flag(self):
        self.login_as(self.trust_user)
        create_test_problem({'organisation': self.test_hospital,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'breach': True})
        resp = self.client.get(self.dashboard_url)
        self.assertContains(resp, '<div class="problem-table__flag__breach">b</div>')


class OrganisationParentTabsTests(AuthorizationTestCase):
    """Test that the tabs shown on Organisation Parent pages link to the right places"""

    def setUp(self):
        super(OrganisationParentTabsTests, self).setUp()
        self.dashboard_url = reverse('org-parent-dashboard', kwargs={'code': self.test_trust.code})
        self.breaches_url = reverse('org-parent-breaches', kwargs={'code': self.test_trust.code})
        self.problems_url = reverse('org-parent-problems', kwargs={'code': self.test_trust.code})
        self.reviews_url = reverse('org-parent-reviews', kwargs={'code': self.test_trust.code})
        self.summary_url = reverse('org-parent-summary', kwargs={'code': self.test_trust.code})
        self.tab_urls = [
            self.dashboard_url,
            self.breaches_url,
            self.problems_url,
            self.reviews_url,
            self.summary_url
        ]
        self.login_as(self.trust_user)

    def _check_tabs(self, page_url, resp):
        for url in self.tab_urls:
            self.assertContains(resp, url, msg_prefix="Response for {0} does not contain url: {1}".format(page_url, url))

    def test_tabs(self):
        for user in [self.trust_user, self.nhs_superuser, self.ccg_user]:
            self.login_as(user)
            for url in self.tab_urls:
                resp = self.client.get(url)
                self._check_tabs(url, resp)
