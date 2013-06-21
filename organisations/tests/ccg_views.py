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
        self.problem = create_test_problem({'organisation': self.test_organisation})
        self.dashboard_url = reverse('ccg-dashboard', kwargs={'code': self.test_ccg.code})

    def test_dashboard_page_exists(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 200)

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
        self.closed_problem = create_test_problem({'organisation': self.test_organisation,
                                                   'status': Problem.RESOLVED})
        closed_problem_response_url = reverse('response-form', kwargs={'pk': self.closed_problem.id})
        self.login_as(self.ccg_user)
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(closed_problem_response_url not in resp.content)

    def test_dashboard_doesnt_show_escalated_problems(self):
        self.escalated_problem = create_test_problem({'organisation': self.test_organisation,
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

        self.login_as(self.other_trust_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 403)

    def test_dashboard_page_is_inaccessible_to_other_ccgs(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 403)

    def test_dashboard_page_highlights_priority_problems(self):
        # Add a priority problem
        self.login_as(self.ccg_user)
        create_test_problem({'organisation': self.test_organisation,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'priority': Problem.PRIORITY_HIGH})
        resp = self.client.get(self.dashboard_url)
        self.assertContains(resp, 'problem-table__highlight')

    def test_dashboard_page_shows_breach_flag(self):
        self.login_as(self.ccg_user)
        create_test_problem({'organisation': self.test_organisation,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'breach': True})
        resp = self.client.get(self.dashboard_url)
        self.assertContains(resp, '<div class="problem-table__flag__breach">b</div>')


class CCGEscalationDashboardTests(AuthorizationTestCase):

    def setUp(self):
        super(CCGEscalationDashboardTests, self).setUp()
        self.escalation_dashboard_url = reverse('ccg-escalation-dashboard', kwargs={'code': self.test_ccg.code})
        self.org_local_escalated_problem = create_test_problem({'organisation': self.test_organisation,
                                                                'status': Problem.ESCALATED,
                                                                'commissioned': Problem.LOCALLY_COMMISSIONED})
        self.org_national_escalated_problem = create_test_problem({'organisation': self.test_organisation,
                                                                   'status': Problem.ESCALATED,
                                                                   'commissioned': Problem.NATIONALLY_COMMISSIONED})
        self.other_org_local_escalated_problem = create_test_problem({'organisation': self.other_test_organisation,
                                                                      'status': Problem.ESCALATED,
                                                                      'commissioned': Problem.LOCALLY_COMMISSIONED})
        self.other_org_national_escalated_problem = create_test_problem({'organisation': self.other_test_organisation,
                                                                         'status': Problem.ESCALATED,
                                                                         'commissioned': Problem.NATIONALLY_COMMISSIONED})

        self.org_local_escalated_acknowledged_problem = create_test_problem({'organisation': self.test_organisation,
                                                                             'status': Problem.ESCALATED_ACKNOWLEDGED,
                                                                             'commissioned': Problem.LOCALLY_COMMISSIONED})
        self.org_local_escalated_resolved_problem = create_test_problem({'organisation': self.test_organisation,
                                                                         'status': Problem.ESCALATED_RESOLVED,
                                                                         'commissioned': Problem.LOCALLY_COMMISSIONED})
        # Add two services to the test org
        self.service_one = create_test_service({'organisation': self.test_organisation})
        self.service_two = create_test_service({'organisation': self.test_organisation,
                                                'name': 'service two',
                                                'service_code': 'SRV222'})
        self.test_organisation.services.add(self.service_one)
        self.test_organisation.services.add(self.service_two)
        self.test_organisation.save()

    def test_dashboard_accessible_to_ccg_users(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.escalation_dashboard_url)
            self.assertEqual(resp.status_code, 200)

    def test_dashboard_is_inacessible_to_anyone_else(self):
        people_who_shouldnt_have_access = [
            self.customer_contact_centre_user,
            self.trust_user,
            self.no_trust_user,
            self.other_trust_user,
            self.second_tier_moderator,
            self.other_ccg_user
        ]

        for user in people_who_shouldnt_have_access:
            self.login_as(user)
            resp = self.client.get(self.escalation_dashboard_url)
            self.assertEqual(resp.status_code, 403, '{0} can access {1} when they shouldn\'t be able to'.format(user.username, self.escalation_dashboard_url))

    def test_dashboard_doesnt_show_escalated_resolved_problem(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertNotContains(resp, self.org_local_escalated_resolved_problem.reference_number)

    def test_dashboard_only_shows_locally_commissioned_problems(self):
        self.login_as(self.ccg_user)
        # Remove the test ccg from the ccgs for this org so that we know access is coming
        # via the escalation_ccg field, not the ccgs association
        self.test_organisation.parent.ccgs.remove(self.test_ccg)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, self.org_local_escalated_problem.reference_number)
        # Does not show other org's problem or nationally commmissioned problem for this org
        self.assertNotContains(resp, self.org_national_escalated_problem.reference_number)
        self.assertNotContains(resp, self.other_org_local_escalated_problem.reference_number)
        self.assertNotContains(resp, self.other_org_national_escalated_problem.reference_number)

    def test_dashboard_hides_ccg_filter(self):
        # This is a CCG-specific dashboard, so no need for the filter
        ccg_filter_to_look_for = 'name="ccg"'

        self.login_as(self.ccg_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertNotContains(resp, ccg_filter_to_look_for)

        self.login_as(self.nhs_superuser)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertNotContains(resp, ccg_filter_to_look_for)

    def test_dashboard_hides_status_filter(self):
        status_filter_to_look_for = 'name="status"'

        self.login_as(self.ccg_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertNotContains(resp, status_filter_to_look_for)

    def test_filters_by_provider_type(self):
        # self.test_organisation is a hospital
        # add a GP org to this ccg
        ccg_gp = create_test_organisation({"ods_code": "GP", "parent": self.test_trust})
        # Add a local commissioned, escalated problem to that new gp
        self.gp_local_escalated_problem = create_test_problem({'organisation': ccg_gp,
                                                               'status': Problem.ESCALATED,
                                                               'commissioned': Problem.LOCALLY_COMMISSIONED})

        self.login_as(self.ccg_user)
        problem_filtered_url = '{0}?organisation_type=hospitals'.format(self.escalation_dashboard_url)
        resp = self.client.get(problem_filtered_url)
        self.assertContains(resp, self.org_local_escalated_problem.reference_number)
        self.assertNotContains(resp, self.gp_local_escalated_problem)
        # These are both associated with a Hospital
        self.assertNotContains(resp, self.other_org_local_escalated_problem.reference_number)
        self.assertNotContains(resp, self.other_org_national_escalated_problem.reference_number)

    def test_filters_by_department(self):
        # Add some problems to the test org against specific services
        service_one_problem = create_test_problem({'organisation': self.test_organisation,
                                                   'service': self.service_one,
                                                   'status': Problem.ESCALATED,
                                                   'commissioned': Problem.LOCALLY_COMMISSIONED})
        service_two_problem = create_test_problem({'organisation': self.test_organisation,
                                                   'service': self.service_two,
                                                   'status': Problem.ESCALATED,
                                                   'commissioned': Problem.LOCALLY_COMMISSIONED})
        department_filtered_url = '{0}?service_code={1}'.format(self.escalation_dashboard_url, self.service_one.service_code)

        # We'll do this as the ccg user, because we should be able to
        self.login_as(self.ccg_user)
        resp = self.client.get(department_filtered_url)

        self.assertContains(resp, service_one_problem.reference_number)
        self.assertNotContains(resp, service_two_problem.reference_number)
        # This doesn't have a service, so we shouldn't see it either
        self.assertNotContains(resp, self.org_local_escalated_problem.reference_number)

    def test_filters_by_problem_category(self):
        cleanliness_problem = create_test_problem({'organisation': self.test_organisation,
                                                   'service': self.service_one,
                                                   'status': Problem.ESCALATED,
                                                   'commissioned': Problem.LOCALLY_COMMISSIONED,
                                                   'category': 'cleanliness'})
        delays_problem = create_test_problem({'organisation': self.test_organisation,
                                              'service': self.service_two,
                                              'status': Problem.ESCALATED,
                                              'commissioned': Problem.LOCALLY_COMMISSIONED,
                                              'category': 'delays'})
        category_filtered_url = '{0}?category=delays'.format(self.escalation_dashboard_url)

        # We'll do this as the ccg user, because we should be able to
        self.login_as(self.ccg_user)
        resp = self.client.get(category_filtered_url)

        self.assertContains(resp, delays_problem.reference_number)
        self.assertNotContains(resp, cleanliness_problem.reference_number)
        # This is in "staff" so shouldn't show either
        self.assertNotContains(resp, self.org_local_escalated_problem.reference_number)

    def test_filters_by_breach(self):
        breach_problem = create_test_problem({'organisation': self.test_organisation,
                                              'service': self.service_two,
                                              'status': Problem.ESCALATED,
                                              'commissioned': Problem.LOCALLY_COMMISSIONED,
                                              'breach': True})
        breach_filtered_url = '{0}?flags=breach'.format(self.escalation_dashboard_url)

        # We'll do this as the ccg user, because we should be able to
        self.login_as(self.ccg_user)
        resp = self.client.get(breach_filtered_url)

        self.assertContains(resp, breach_problem.reference_number)
        # This is not a breach, so shouldn't show
        self.assertNotContains(resp, self.org_local_escalated_problem.reference_number)

    def test_dashboard_shows_breach_flag(self):
        # Add a breach problem that should show up
        create_test_problem({'organisation': self.test_organisation,
                             'service': self.service_two,
                             'status': Problem.ESCALATED,
                             'commissioned': Problem.LOCALLY_COMMISSIONED,
                             'breach': True})
        self.login_as(self.ccg_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, '<div class="problem-table__flag__breach">b</div>')

    def test_dashboard_shows_escalation_flag(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, '<div class="problem-table__flag__escalate">e</div>')

    def test_dashboard_highlights_priority_problems(self):
        self.login_as(self.ccg_user)
        # Up the priority of a problem
        self.org_local_escalated_problem.priority = Problem.PRIORITY_HIGH
        self.org_local_escalated_problem.save()
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, 'problem-table__highlight')


class CCGBreachDashboardTests(AuthorizationTestCase):

    def setUp(self):
        super(CCGBreachDashboardTests, self).setUp()
        self.breach_dashboard_url = reverse('ccg-escalation-breaches', kwargs={'code': self.test_ccg.code})
        self.org_breach_problem = create_test_problem({'organisation': self.test_organisation,
                                                       'breach': True})
        self.other_org_breach_problem = create_test_problem({'organisation': self.other_test_organisation,
                                                             'breach': True})
        self.org_problem = create_test_problem({'organisation': self.test_organisation})

    def test_dashboard_accessible_to_ccg_users(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.breach_dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.breach_dashboard_url)
            self.assertEqual(resp.status_code, 200)

    def test_dashboard_is_inacessible_to_anyone_else(self):
        people_who_shouldnt_have_access = [
            self.customer_contact_centre_user,
            self.trust_user,
            self.no_trust_user,
            self.other_trust_user,
            self.second_tier_moderator,
            self.other_ccg_user
        ]

        for user in people_who_shouldnt_have_access:
            self.login_as(user)
            resp = self.client.get(self.breach_dashboard_url)
            self.assertEqual(resp.status_code, 403, '{0} can access {1} when they shouldn\'t be able to'.format(user.username, self.breach_dashboard_url))

    def test_dashboard_only_shows_breach_problems(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.breach_dashboard_url)
        self.assertContains(resp, self.org_breach_problem.reference_number)
        self.assertNotContains(resp, self.org_problem.reference_number)

    def test_dashboard_limits_problems_to_ccg(self):
        # Should show the same problem to everyone
        for user in (self.ccg_user, self.nhs_superuser):
            self.login_as(user)
            resp = self.client.get(self.breach_dashboard_url)
            self.assertContains(resp, self.org_breach_problem.reference_number)
            self.assertNotContains(resp, self.other_org_breach_problem.reference_number)

    def test_dashboard_shows_breach_flag(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.breach_dashboard_url)
        self.assertContains(resp, '<div class="problem-table__flag__breach">b</div>')

    def test_dashboard_shows_escalation_flag(self):
        self.login_as(self.ccg_user)
        # Make the breach problem escalated too
        self.org_breach_problem.status = Problem.ESCALATED
        self.org_breach_problem.commissioned = Problem.LOCALLY_COMMISSIONED
        self.org_breach_problem.save()
        resp = self.client.get(self.breach_dashboard_url)
        self.assertContains(resp, '<div class="problem-table__flag__escalate">e</div>')

    def test_dashboard_highlights_priority_problems(self):
        self.login_as(self.ccg_user)
        # Up the priority of the breach problem
        self.org_breach_problem.priority = Problem.PRIORITY_HIGH
        self.org_breach_problem.save()
        resp = self.client.get(self.breach_dashboard_url)
        self.assertContains(resp, 'problem-table__highlight')


@override_settings(SUMMARY_THRESHOLD=None)
class CCGSummaryTests(AuthorizationTestCase):

    def setUp(self):
        super(CCGSummaryTests, self).setUp()
        self.summary_url = reverse('ccg-summary', kwargs={'code': self.test_ccg.code})
        create_test_problem({'organisation': self.test_organisation})
        create_test_problem({'organisation': self.other_test_organisation,
                             'publication_status': Problem.PUBLISHED,
                             'status': Problem.ABUSIVE})
        self.login_as(self.ccg_user)

    def test_summary_page_authorization(self):

        tests = (
            # (user, permitted? )
            (None,                               False),
            (self.trust_user,                    False),
            (self.case_handler,                  False),
            (self.second_tier_moderator,         False),
            (self.other_ccg_user,                False),
            (self.customer_contact_centre_user,  False),
            (self.no_ccg_user,                   False),

            (self.superuser,                     True),
            (self.nhs_superuser,                 True),
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
            for trust in self.test_ccg.organisation_parents.all():
                for org in trust.organisations.all():
                    self.assertContains(resp, org.name)
            for trust in self.other_test_ccg.organisation_parents.all():
                for org in trust.organisations.all():
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
        create_test_problem({'organisation': self.test_organisation,
                             'breach': True})

        breach_filtered_url = '{0}?flags=breach'.format(self.summary_url)
        resp = self.client.get(breach_filtered_url)
        test_org_record = resp.context['table'].rows[0].record
        self.assertEqual(test_org_record['week'], 1)

    def test_summary_page_filters_by_formal_complaint(self):
        # Add a formal_complaint problem
        create_test_problem({'organisation': self.test_organisation,
                             'formal_complaint': True})

        formal_complaint_filtered_url = '{0}?flags=formal_complaint'.format(self.summary_url)
        resp = self.client.get(formal_complaint_filtered_url)
        test_org_record = resp.context['table'].rows[0].record
        self.assertEqual(test_org_record['week'], 1)


class CCGTabsTests(AuthorizationTestCase):
    """Test that the tabs shown on trust pages link to the right places"""

    def setUp(self):
        super(CCGTabsTests, self).setUp()
        self.dashboard_url = reverse('ccg-dashboard', kwargs={'code': self.test_ccg.code})
        self.escalation_dashboard_url = reverse('ccg-escalation-dashboard', kwargs={'code': self.test_ccg.code})
        self.breaches_url = reverse('ccg-escalation-breaches', kwargs={'code': self.test_ccg.code})
        self.summary_url = reverse('ccg-summary', kwargs={'code': self.test_ccg.code})
        self.tab_urls = [
            self.dashboard_url,
            self.escalation_dashboard_url,
            self.breaches_url,
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
