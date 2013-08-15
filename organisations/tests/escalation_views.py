# encoding: utf-8
# Django imports
from django.core.urlresolvers import reverse

# App imports
from issues.models import Problem

from . import (create_test_problem,
               create_test_service,
               AuthorizationTestCase)


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

    def test_dashboard_highlights_priority_problems(self):
        # Up the priority of the breach problem
        self.org_breach_problem.priority = Problem.PRIORITY_HIGH
        self.org_breach_problem.save()

        for user in (self.customer_contact_centre_user, self.nhs_superuser):
            self.login_as(user)
            resp = self.client.get(self.breach_dashboard_url)
            self.assertContains(resp, 'problem-table__highlight')
