# Django imports
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

# App imports
from issues.models import Problem

from . import (create_test_problem,
               create_test_service,
               create_test_organisation,
               AuthorizationTestCase)


class CCGDashboardTests(AuthorizationTestCase):

    def setUp(self):
        super(CCGDashboardTests, self).setUp()
        self.problem = create_test_problem({'organisation': self.test_hospital})
        self.dashboard_url = reverse('ccg-dashboard', kwargs={'code': self.test_ccg.code})

    def test_dashboard_page_exists(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_raises_404_not_500(self):
        # Issue #878 - views inheriting from CCGAwareViewMixin
        # didn't catch CCG.DoesNotExist and raise an Http404
        # so we got a 500 instead
        missing_url = reverse('ccg-dashboard', kwargs={'code': 'missing'})
        self.login_as(self.nhs_superuser)  # Superuser to avoid being redirected to login first
        resp = self.client.get(missing_url)
        self.assertEqual(resp.status_code, 404)

    def test_dashboard_page_shows_ccg_name(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(self.test_ccg.name in resp.content)

    def test_dashboard_shows_problems(self):
        self.login_as(self.ccg_user)
        response_url = reverse('response-form', kwargs={'pk': self.problem.id})
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(response_url in resp.content)

    def test_dashboard_doesnt_show_closed_problems(self):
        self.closed_problem = create_test_problem({'organisation': self.test_hospital,
                                                   'status': Problem.RESOLVED})
        closed_problem_response_url = reverse('response-form', kwargs={'pk': self.closed_problem.id})
        self.login_as(self.ccg_user)
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(closed_problem_response_url not in resp.content)

    def test_dashboard_doesnt_show_escalated_problems(self):
        self.escalated_problem = create_test_problem({'organisation': self.test_hospital,
                                                      'status': Problem.ESCALATED,
                                                      'commissioned': Problem.LOCALLY_COMMISSIONED})
        escalated_problem_response_url = reverse('response-form', kwargs={'pk': self.escalated_problem.id})
        self.login_as(self.ccg_user)
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(escalated_problem_response_url not in resp.content)

    def test_dashboard_page_is_inaccessible_to_anon_users(self):
        expected_login_url = "{0}?next={1}".format(self.login_url, self.dashboard_url)
        resp = self.client.get(self.dashboard_url)
        self.assertRedirects(resp, expected_login_url)

    def test_dashboard_page_is_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.dashboard_url)
            self.assertEqual(resp.status_code, 200)

    def test_dashboard_page_is_inaccessible_to_trust_users(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 403)

        self.login_as(self.gp_surgery_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 403)

    def test_dashboard_page_is_inaccessible_to_other_ccgs(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 403)

    def test_dashboard_page_highlights_priority_problems(self):
        # Add a priority problem
        self.login_as(self.ccg_user)
        create_test_problem({'organisation': self.test_hospital,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'priority': Problem.PRIORITY_HIGH})
        resp = self.client.get(self.dashboard_url)
        self.assertContains(resp, 'problem-table__highlight')

    def test_dashboard_page_shows_breach_flag(self):
        self.login_as(self.ccg_user)
        create_test_problem({'organisation': self.test_hospital,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'breach': True})
        resp = self.client.get(self.dashboard_url)
        self.assertContains(resp, '<div class="problem-table__flag__breach">b</div>')


@override_settings(SUMMARY_THRESHOLD=None)
class CCGSummaryTests(AuthorizationTestCase):

    def setUp(self):
        super(CCGSummaryTests, self).setUp()
        self.summary_url = reverse('ccg-summary', kwargs={'code': self.test_ccg.code})
        create_test_problem({'organisation': self.test_hospital})
        create_test_problem({'organisation': self.test_gp_branch,
                             'publication_status': Problem.PUBLISHED,
                             'status': Problem.ABUSIVE})
        self.login_as(self.ccg_user)

    def test_summary_page_authorization(self):

        tests = (
            # (user, permitted? )
            (None,                               False),
            (self.trust_user,                    False),
            (self.second_tier_moderator,         False),
            (self.other_ccg_user,                False),
            (self.no_ccg_user,                   False),

            (self.superuser,                     True),
            (self.nhs_superuser,                 True),
            (self.case_handler,                  True),
            (self.customer_contact_centre_user,  True),
            (self.ccg_user,                      True),
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

    def test_organisations_limited_to_ccg(self):
        for user in [self.ccg_user, self.nhs_superuser]:
            self.login_as(user)

            # check they see orgs for test_ccg and not for other_ccg
            resp = self.client.get(self.summary_url)
            for org_parent in self.test_ccg.organisation_parents.all():
                for org in org_parent.organisations.all():
                    self.assertContains(resp, org.name)
            for org_parent in self.other_test_ccg.organisation_parents.all():
                for org in org_parent.organisations.all():
                    self.assertNotContains(resp, org.name)

    def test_ccg_filter_hidden(self):
        # This is a CCG-specific dashboard, so no need for the filter
        ccg_filter_to_look_for = 'name="ccg"'

        self.login_as(self.ccg_user)
        resp = self.client.get(self.summary_url)
        self.assertNotContains(resp, ccg_filter_to_look_for)

        self.login_as(self.nhs_superuser)
        resp = self.client.get(self.summary_url)
        self.assertNotContains(resp, ccg_filter_to_look_for)

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
        test_org_record = resp.context['table'].rows[0].record
        self.assertEqual(test_org_record['week'], 1)

    def test_summary_page_filters_by_formal_complaint(self):
        # Add a formal_complaint problem
        create_test_problem({'organisation': self.test_hospital,
                             'formal_complaint': True})

        formal_complaint_filtered_url = '{0}?flags=formal_complaint'.format(self.summary_url)
        resp = self.client.get(formal_complaint_filtered_url)
        test_org_record = resp.context['table'].rows[0].record
        self.assertEqual(test_org_record['week'], 1)


class CCGTabsTests(AuthorizationTestCase):
    """Test that the tabs shown on ccg pages link to the right places"""

    def setUp(self):
        super(CCGTabsTests, self).setUp()
        self.dashboard_url = reverse('ccg-dashboard', kwargs={'code': self.test_ccg.code})
        self.summary_url = reverse('ccg-summary', kwargs={'code': self.test_ccg.code})
        self.tab_urls = [
            self.dashboard_url,
            self.summary_url
        ]
        self.login_as(self.trust_user)

    def _check_tabs(self, page_url, resp):
        for url in self.tab_urls:
            self.assertContains(resp, url, msg_prefix="Response for {0} does not contain url: {1}".format(page_url, url))

    def test_tabs(self):
        for user in [self.nhs_superuser, self.ccg_user]:
            self.login_as(user)
            for url in self.tab_urls:
                resp = self.client.get(url)
                self._check_tabs(url, resp)
