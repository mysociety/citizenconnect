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


class OrganisationSummaryTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationSummaryTests, self).setUp()

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

        self.public_summary_url = reverse('public-org-summary', kwargs={'ods_code': self.test_organisation.ods_code,
                                                                        'cobrand': 'choices'})
        self.private_summary_url = reverse('private-org-summary', kwargs={'ods_code': self.test_organisation.ods_code})
        self.urls = [self.public_summary_url, self.private_summary_url]

    def test_summary_page_exists(self):
        for url in self.urls:
            self.login_as(self.trust_user)
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_summary_page_shows_organisation_name(self):
        for url in self.urls:
            self.login_as(self.trust_user)
            resp = self.client.get(url)
            self.assertTrue(self.test_organisation.name in resp.content)

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

        self.assertEqual(problems_by_status[7]['all_time'], 1)
        self.assertEqual(problems_by_status[7]['week'], 1)
        self.assertEqual(problems_by_status[7]['four_weeks'], 1)
        self.assertEqual(problems_by_status[7]['six_months'], 1)
        self.assertEqual(problems_by_status[7]['description'], 'Abusive/Vexatious')

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
        create_test_problem({'organisation': self.test_organisation,
                             'breach': True})

        self.login_as(self.trust_user)
        resp = self.client.get(self.private_summary_url + '?flags=breach')

        problems_by_status = resp.context['problems_by_status']
        self.assertEqual(problems_by_status[0]['all_time'], 1)
        self.assertEqual(problems_by_status[0]['week'], 1)
        self.assertEqual(problems_by_status[0]['four_weeks'], 1)
        self.assertEqual(problems_by_status[0]['six_months'], 1)

    def test_summary_page_applies_formal_complaint_filter_on_private_pages(self):
        create_test_problem({'organisation': self.test_organisation,
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
        self.assertContains(resp, '<td class="average_time_to_acknowledge" id="status_7_time_to_acknowledge">—</td>')
        self.assertContains(resp, '<td class="average_time_to_address" id="status_7_time_to_address">—</td>')
        self.assertContains(resp, '<td class="happy_service" id="status_7_happy_service">—</td>')
        self.assertContains(resp, '<td class="happy_outcome" id="status_7_happy_outcome">—</td>')

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
        self.login_as(self.other_trust_user)
        resp = self.client.get(self.private_summary_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_summary_page_is_inaccessible_to_other_ccgs(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.private_summary_url)
        self.assertEqual(resp.status_code, 403)


class OrganisationProblemsTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationProblemsTests, self).setUp()

        # Organisations
        self.hospital = create_test_organisation({'organisation_type': 'hospitals',
                                                  'ods_code': 'ABC123',
                                                  'trust': self.test_trust})
        self.gp = create_test_organisation({'organisation_type': 'gppractices',
                                            'ods_code': 'DEF456',
                                            'trust': self.other_test_trust})

        # Useful urls
        self.public_hospital_problems_url = reverse('public-org-problems',
                                                    kwargs={'ods_code': self.hospital.ods_code,
                                                            'cobrand': 'choices'})
        self.public_gp_problems_url = reverse('public-org-problems',
                                              kwargs={'ods_code': self.gp.ods_code,
                                                      'cobrand': 'choices'})

        # Problems
        self.staff_problem = create_test_problem({'category': 'staff',
                                                  'organisation': self.hospital,
                                                  'publication_status': Problem.PUBLISHED,
                                                  'moderated_description': "Moderated description"})
        # Add an explicitly public and an explicitly private problem to test
        # privacy is respected
        self.public_problem = create_test_problem({'organisation': self.hospital})
        self.private_problem = create_test_problem({'organisation': self.hospital, 'public': False})

    def test_shows_services_for_hospitals(self):
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertContains(resp, '<th class="service">Department</th>', count=1, status_code=200)

    def test_shows_time_limits_for_hospitals(self):
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertContains(resp, '<th class="time_to_acknowledge">Acknowledge</th>', count=1, status_code=200)
        self.assertContains(resp, '<th class="time_to_address">Address</th>', count=1, status_code=200)

    def test_no_services_for_gps(self):
        resp = self.client.get(self.public_gp_problems_url)
        self.assertNotContains(resp, '<th class="service">Department</th>')

    def test_no_time_limits_for_gps(self):
        resp = self.client.get(self.public_gp_problems_url)
        self.assertNotContains(resp, '<th class="time_to_acknowledge">Acknowledge</th>')
        self.assertNotContains(resp, '<th class="time_to_address">Address</th>')

    def test_public_page_exists_and_is_accessible_to_anyone(self):
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertEqual(resp.status_code, 200)

    def test_public_page_links_to_public_problems(self):
        staff_problem_url = reverse('problem-view', kwargs={'pk': self.staff_problem.id,
                                                            'cobrand': 'choices'})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertContains(resp, staff_problem_url)

    def test_public_page_shows_private_problems(self):
        # Add a private problem
        private_problem = create_test_problem({'organisation': self.hospital,
                                               'publication_status': Problem.PUBLISHED,
                                               'public': False})
        private_problem_url = reverse('problem-view', kwargs={'pk': self.private_problem.id,
                                                              'cobrand': 'choices'})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertTrue(private_problem.reference_number in resp.content)
        self.assertTrue(private_problem.summary in resp.content)
        self.assertTrue(private_problem_url in resp.content)

    def test_public_page_doesnt_show_rejected_problems(self):
        # Add some problems which shouldn't show up
        rejected_problem = create_test_problem({'organisation': self.hospital,
                                                'publication_status': Problem.REJECTED})
        rejected_problem_url = reverse('problem-view', kwargs={'pk': rejected_problem.id,
                                                               'cobrand': 'choices'})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertTrue(rejected_problem_url not in resp.content)

    def test_public_page_shows_not_moderated_problems(self):
        unmoderated_problem = create_test_problem({'organisation': self.hospital,
                                                   'publication_status': Problem.NOT_MODERATED})
        unmoderated_problem_url = reverse('problem-view', kwargs={'pk': unmoderated_problem.id,
                                                                  'cobrand': 'choices'})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertTrue(unmoderated_problem_url in resp.content)

    def test_filters_by_status(self):
        # Add a problem in a different status that would show up
        resolved_problem = create_test_problem({'organisation': self.hospital,
                                                'status': Problem.ACKNOWLEDGED,
                                                'publication_status': Problem.PUBLISHED,
                                                'moderated_description': 'Moderated'})
        status_filtered_url = "{0}?status={1}".format(self.public_hospital_problems_url, Problem.NEW)
        resp = self.client.get(status_filtered_url)
        self.assertContains(resp, self.staff_problem.reference_number)
        self.assertNotContains(resp, resolved_problem.reference_number)

    def test_shows_only_public_statuses_on_public_page(self):
        resp = self.client.get(self.public_hospital_problems_url)
        for status, label in Problem.STATUS_CHOICES:
            if status in Problem.HIDDEN_STATUSES:
                self.assertNotContains(resp, '<option value="{0}">{1}</option>'.format(status, label))

    def test_ignores_private_statuses_on_public_page(self):
        # Even if we manually hack the url, it shouldn't do any filtering
        # Add a problem in a different status that would show up
        abusive_problem = create_test_problem({'organisation': self.hospital,
                                               'status': Problem.ABUSIVE,
                                               'publication_status': Problem.PUBLISHED,
                                               'moderated_description': 'Moderated'})
        status_filtered_url = "{0}?status={1}".format(self.public_hospital_problems_url, Problem.ABUSIVE)
        resp = self.client.get(status_filtered_url)
        self.assertContains(resp, self.staff_problem.reference_number)
        self.assertNotContains(resp, abusive_problem.reference_number)

    def test_filters_by_category(self):
        # Add a problem in a different status that would show up
        cleanliness_problem = create_test_problem({'organisation': self.hospital,
                                                   'category': 'cleanliness',
                                                   'publication_status': Problem.PUBLISHED,
                                                   'moderated_description': 'Moderated'})
        category_filtered_url = "{0}?category=cleanliness".format(self.public_hospital_problems_url)
        resp = self.client.get(category_filtered_url)
        self.assertContains(resp, cleanliness_problem.reference_number)
        self.assertNotContains(resp, self.staff_problem.reference_number)

    def test_public_page_does_not_have_breach_filter(self):
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, '<option value="breach">')

    def test_public_page_does_not_have_formal_complaint_filter(self):
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, '<option value="formal_complaint">')

    def test_doesnt_show_service_filter_for_gp(self):
        resp = self.client.get(self.public_gp_problems_url)
        self.assertNotContains(resp, '<select name="service_id" id="id_service_id">')

    def test_filters_by_service_for_hospital(self):
        # Add a service to the test hospital
        service = create_test_service({'organisation': self.hospital})
        # Add a problem about a specific service
        service_problem = create_test_problem({'organisation': self.hospital,
                                               'service': service,
                                               'publication_status': Problem.PUBLISHED,
                                               'moderated_description': 'Moderated'})
        service_filtered_url = "{0}?service_id={1}".format(self.public_hospital_problems_url, service.id)
        resp = self.client.get(service_filtered_url)
        self.assertContains(resp, service_problem.reference_number)
        self.assertNotContains(resp, self.staff_problem.reference_number)

    def test_column_sorting(self):
        # Test that each of the columns we expect to be sortable, is.
        # ISSUE-498 - this raised a 500 on 'resolved' because resolved was not a model field
        columns = ('reference_number',
                   'created',
                   'status',
                   'resolved')
        for column in columns:
            sorted_url = "{0}?sort={1}".format(self.public_hospital_problems_url, column)
            resp = self.client.get(sorted_url)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.context['table'].data.ordering, [column])

    def test_public_page_doesnt_highlight_priority_problems(self):
        # Add a priority problem
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'priority': Problem.PRIORITY_HIGH})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, 'problem-table__highlight')

    def test_public_page_doesnt_show_breach_flag(self):
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'breach': True})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, '<div class="problem-table__flag__breach">b</div>')

    def test_public_page_doesnt_show_escalated_flag(self):
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'status': Problem.ESCALATED,
                             'commissioned': Problem.LOCALLY_COMMISSIONED})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, '<div class="problem-table__flag__escalate">e</div>')

    def test_public_page_shows_public_summary(self):
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'description': 'private description',
                             'moderated_description': 'public description'})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, 'private description')
        self.assertContains(resp, 'public description')


class OrganisationTabsTests(AuthorizationTestCase):
    """Test that the tabs shown on trust pages link to the right places"""

    def setUp(self):
        super(OrganisationTabsTests, self).setUp()
        self.summary_url = reverse('public-org-summary', kwargs={'ods_code': self.test_organisation.ods_code, 'cobrand': 'choices'})
        self.problems_url = reverse('public-org-problems', kwargs={'ods_code': self.test_organisation.ods_code, 'cobrand': 'choices'})
        self.reviews_url = reverse('review-organisation-list', kwargs={'ods_code': self.test_organisation.ods_code, 'cobrand': 'choices'})
        self.tab_urls = [
            self.reviews_url,
            self.problems_url,
            self.summary_url
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
        for user in [self.nhs_superuser, self.ccg_user, self.trust_user, self.other_trust_user, self.other_ccg_user]:
            self.login_as(user)
            for url in self.tab_urls:
                resp = self.client.get(url)
                self._check_tabs(url, resp)
