# encoding: utf-8
from decimal import Decimal

# Django imports
from django.core.urlresolvers import reverse

# App imports
from issues.models import Problem

from . import (create_test_problem,
               create_test_organisation,
               create_test_service,
               AuthorizationTestCase)


class TrustSummaryTests(AuthorizationTestCase):

    def setUp(self):
        super(TrustSummaryTests, self).setUp()

        self.service = create_test_service({'organisation': self.test_organisation})

        # Problems
        atts = {'organisation': self.test_organisation}
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

        self.trust_summary_url = reverse('trust-summary', kwargs={'code': self.test_organisation.trust.code})

    def test_summary_page_exists(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url)
        self.assertEqual(resp.status_code, 200)

    def test_summary_page_shows_trust_name(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_summary_url)
        self.assertTrue(self.test_organisation.trust.name in resp.content)

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
        create_test_problem({'organisation': self.test_organisation,
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
        create_test_problem({'organisation': self.test_organisation,
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

        self.assertEqual(problems_by_status[7]['all_time'], 1)
        self.assertEqual(problems_by_status[7]['week'], 1)
        self.assertEqual(problems_by_status[7]['four_weeks'], 1)
        self.assertEqual(problems_by_status[7]['six_months'], 1)
        self.assertEqual(problems_by_status[7]['description'], 'Abusive/Vexatious')

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
        self.assertContains(resp, '<td class="average_time_to_acknowledge" id="status_7_time_to_acknowledge">—</td>')
        self.assertContains(resp, '<td class="average_time_to_address" id="status_7_time_to_address">—</td>')
        self.assertContains(resp, '<td class="happy_service" id="status_7_happy_service">—</td>')
        self.assertContains(resp, '<td class="happy_outcome" id="status_7_happy_outcome">—</td>')

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
        self.login_as(self.other_trust_user)
        resp = self.client.get(self.trust_summary_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_summary_page_is_inaccessible_to_other_ccgs(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.trust_summary_url)
        self.assertEqual(resp.status_code, 403)


class TrustProblemsTests(AuthorizationTestCase):

    def setUp(self):
        super(TrustProblemsTests, self).setUp()

        # Organisations
        self.hospital = create_test_organisation({'organisation_type': 'hospitals',
                                                  'ods_code': 'ABC123',
                                                  'trust': self.test_trust})
        self.gp = create_test_organisation({'organisation_type': 'gppractices',
                                            'ods_code': 'DEF456',
                                            'trust': self.other_test_trust})

        # Useful urls
        self.trust_problems_url = reverse('trust-problems',
                                          kwargs={'code': self.hospital.trust.code})
        self.other_trust_problems_url = reverse('trust-problems',
                                                kwargs={'code': self.gp.trust.code})

        # Problems
        self.staff_problem = create_test_problem({'category': 'staff',
                                                  'organisation': self.hospital,
                                                  'moderated': Problem.MODERATED,
                                                  'publication_status': Problem.PUBLISHED,
                                                  'moderated_description': "Moderated description"})
        # Add an explicitly public and an explicitly private problem to test
        # privacy is respected
        self.public_problem = create_test_problem({'organisation': self.hospital})
        self.private_problem = create_test_problem({'organisation': self.hospital, 'public': False})

    def test_private_page_exists(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_problems_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_page_links_to_problems(self):
        self.login_as(self.trust_user)
        response_url = reverse('response-form', kwargs={'pk': self.staff_problem.id})
        resp = self.client.get(self.trust_problems_url)
        self.assertTrue(response_url in resp.content)

    def test_private_page_shows_hidden_private_and_unmoderated_problems(self):
        # Add some extra problems
        unmoderated_problem = create_test_problem({'organisation': self.hospital})
        unmoderated_response_url = reverse('response-form', kwargs={'pk': unmoderated_problem.id})
        hidden_problem = create_test_problem({'organisation': self.hospital,
                                              'moderated': Problem.MODERATED,
                                              'publication_status': Problem.HIDDEN})
        hidden_response_url = reverse('response-form', kwargs={'pk': hidden_problem.id})
        private_problem = create_test_problem({'organisation': self.hospital,
                                               'moderated': Problem.MODERATED,
                                               'publication_status': Problem.PUBLISHED,
                                               'public': False})
        private_response_url = reverse('response-form', kwargs={'pk': self.private_problem.id})
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_problems_url)
        self.assertTrue(unmoderated_response_url in resp.content)
        self.assertTrue(hidden_response_url in resp.content)
        self.assertTrue(private_response_url in resp.content)
        self.assertTrue(private_problem.private_summary in resp.content)

    def test_private_page_is_inaccessible_to_anon_users(self):
        expected_login_url = "{0}?next={1}".format(self.login_url, self.trust_problems_url)
        resp = self.client.get(self.trust_problems_url)
        self.assertRedirects(resp, expected_login_url)

    def test_private_pages_are_accessible_to_all_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.trust_problems_url)
            self.assertEqual(resp.status_code, 200)
            resp = self.client.get(self.other_trust_problems_url)
            self.assertEqual(resp.status_code, 200)

    def test_private_page_is_inaccessible_to_other_providers(self):
        self.login_as(self.other_trust_user)
        resp = self.client.get(self.trust_problems_url)
        self.assertEqual(resp.status_code, 403)
        self.login_as(self.trust_user)
        resp = self.client.get(self.other_trust_problems_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_page_is_inaccessible_to_other_ccgs(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.trust_problems_url)
        self.assertEqual(resp.status_code, 403)
        self.login_as(self.ccg_user)
        resp = self.client.get(self.other_trust_problems_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_page_is_accessible_to_ccg(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.trust_problems_url)
        self.assertEqual(resp.status_code, 200)

    def test_shows_all_statuses_on_private_page(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.trust_problems_url)
        for status, label in Problem.STATUS_CHOICES:
            self.assertContains(resp, '<option value="{0}">{1}</option>'.format(status, label))

    def test_private_page_filters_by_breach(self):
        # Add a breach problem
        self.login_as(self.trust_user)
        breach_problem = create_test_problem({'organisation': self.hospital,
                                              'breach': True,
                                              'moderated': Problem.MODERATED,
                                              'publication_status': Problem.PUBLISHED,
                                              'moderated_description': 'Moderated'})
        breach_filtered_url = "{0}?flags=breach".format(self.trust_problems_url)
        resp = self.client.get(breach_filtered_url)
        self.assertContains(resp, breach_problem.reference_number)
        self.assertNotContains(resp, self.staff_problem.reference_number)

    def test_private_page_highlights_priority_problems(self):
        # Add a priority problem
        self.login_as(self.trust_user)
        create_test_problem({'organisation': self.hospital,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'priority': Problem.PRIORITY_HIGH})
        resp = self.client.get(self.trust_problems_url)
        self.assertContains(resp, 'problem-table__highlight')

    def test_private_page_shows_breach_flag(self):
        self.login_as(self.trust_user)
        create_test_problem({'organisation': self.hospital,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'breach': True})
        resp = self.client.get(self.trust_problems_url)
        self.assertContains(resp, '<div class="problem-table__flag__breach">b</div>')

    def test_private_page_shows_escalated_flag(self):
        self.login_as(self.trust_user)
        create_test_problem({'organisation': self.hospital,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'status': Problem.ESCALATED,
                             'commissioned': Problem.LOCALLY_COMMISSIONED})
        resp = self.client.get(self.trust_problems_url)
        self.assertContains(resp, '<div class="problem-table__flag__escalate">e</div>')

    def test_private_page_shows_private_summary(self):
        self.login_as(self.trust_user)
        create_test_problem({'organisation': self.hospital,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'description': 'private description',
                             'moderated_description': 'public description'})
        resp = self.client.get(self.trust_problems_url)
        self.assertContains(resp, 'private description')
        self.assertNotContains(resp, 'public description')

    def test_private_page_includes_provider_name(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_problems_url)
        self.assertContains(resp, '<th class="orderable provider_name sortable">')
        self.assertContains(resp, self.test_organisation.name)


class TrustDashboardTests(AuthorizationTestCase):

    def setUp(self):
        super(TrustDashboardTests, self).setUp()
        self.problem = create_test_problem({'organisation': self.test_organisation})
        self.dashboard_url = reverse('trust-dashboard', kwargs={'code': self.test_organisation.trust.code})

    def test_dashboard_page_exists(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_page_shows_trust_name(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(self.test_organisation.trust.name in resp.content)

    def test_dashboard_shows_problems(self):
        self.login_as(self.trust_user)
        response_url = reverse('response-form', kwargs={'pk': self.problem.id})
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(response_url in resp.content)

    def test_dashboard_doesnt_show_closed_problems(self):
        self.closed_problem = create_test_problem({'organisation': self.test_organisation,
                                                   'status': Problem.RESOLVED})
        closed_problem_response_url = reverse('response-form', kwargs={'pk': self.closed_problem.id})
        self.login_as(self.trust_user)
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(closed_problem_response_url not in resp.content)

    def test_dashboard_doesnt_show_escalated_problems(self):
        self.escalated_problem = create_test_problem({'organisation': self.test_organisation,
                                                      'status': Problem.ESCALATED,
                                                      'commissioned': Problem.LOCALLY_COMMISSIONED})
        escalated_problem_response_url = reverse('response-form', kwargs={'pk': self.escalated_problem.id})
        self.login_as(self.trust_user)
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

    def test_dashboard_page_is_inaccessible_to_other_trusts(self):
        self.login_as(self.other_trust_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 403)

    def test_dashboard_page_is_inaccessible_to_other_ccgs(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 403)

    def test_dashboard_page_highlights_priority_problems(self):
        # Add a priority problem
        self.login_as(self.trust_user)
        create_test_problem({'organisation': self.test_organisation,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'priority': Problem.PRIORITY_HIGH})
        resp = self.client.get(self.dashboard_url)
        self.assertContains(resp, 'problem-table__highlight')

    def test_dashboard_page_shows_breach_flag(self):
        self.login_as(self.trust_user)
        create_test_problem({'organisation': self.test_organisation,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'breach': True})
        resp = self.client.get(self.dashboard_url)
        self.assertContains(resp, '<div class="problem-table__flag__breach">b</div>')


class TrustBreachesTests(AuthorizationTestCase):

    def setUp(self):
        super(TrustBreachesTests, self).setUp()
        self.breach_dashboard_url = reverse('trust-breaches', kwargs={'code': self.test_trust.code})
        self.org_breach_problem = create_test_problem({'organisation': self.test_organisation,
                                                       'breach': True})
        self.other_org_breach_problem = create_test_problem({'organisation': self.other_test_organisation,
                                                             'breach': True})
        self.org_problem = create_test_problem({'organisation': self.test_organisation})

    def test_dashboard_accessible_to_provider(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.breach_dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_is_inacessible_to_other_people(self):
        people_who_shouldnt_have_access = [
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