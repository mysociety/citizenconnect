# encoding: utf-8
import os
from mock import MagicMock
import json
import urllib
from decimal import Decimal
import logging

# Django imports
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

# App imports
from issues.models import Problem

import organisations
from ..models import Organisation
from . import create_test_problem, create_test_organisation, create_test_service, create_test_ccg, AuthorizationTestCase
from organisations.forms import OrganisationFinderForm


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
            self.login_as(self.provider)
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_summary_page_shows_organisation_name(self):
        for url in self.urls:
            self.login_as(self.provider)
            resp = self.client.get(url)
            self.assertTrue(self.test_organisation.name in resp.content)

    def test_private_summary_page_shows_all_problems(self):
        self.login_as(self.provider)
        resp = self.client.get(self.private_summary_url)
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
        self.assertEqual(problems_by_status[2]['description'], 'Responded to')

        self.assertEqual(problems_by_status[7]['all_time'], 1)
        self.assertEqual(problems_by_status[7]['week'], 1)
        self.assertEqual(problems_by_status[7]['four_weeks'], 1)
        self.assertEqual(problems_by_status[7]['six_months'], 1)
        self.assertEqual(problems_by_status[7]['description'], 'Abusive/Vexatious')

    def test_public_summary_page_only_shows_visible_problems(self):
        self.login_as(self.provider)
        resp = self.client.get(self.public_summary_url)
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
        self.assertEqual(problems_by_status[2]['description'], 'Responded to')

    def test_summary_page_applies_problem_category_filter(self):
        for url in self.urls:
            self.login_as(self.provider)
            resp = self.client.get(url + '?category=cleanliness')

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
            self.login_as(self.provider)
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

        self.login_as(self.provider)
        resp = self.client.get(self.private_summary_url + '?breach=True')

        problems_by_status = resp.context['problems_by_status']
        self.assertEqual(problems_by_status[0]['all_time'], 1)
        self.assertEqual(problems_by_status[0]['week'], 1)
        self.assertEqual(problems_by_status[0]['four_weeks'], 1)
        self.assertEqual(problems_by_status[0]['six_months'], 1)

    def test_public_summary_page_does_not_have_breach_filter(self):
        resp = self.client.get(self.public_summary_url)
        self.assertNotContains(resp, '<select name="breach" id="id_breach">')

    def test_summary_page_gets_survey_data_for_problems_in_visible_statuses(self):
        for url in self.urls:
            self.login_as(self.provider)
            resp = self.client.get(url)
            issues_total = resp.context['issues_total']
            self.assertEqual(issues_total['happy_service'], 0.666666666666667)
            self.assertEqual(issues_total['happy_outcome'], 1.0)

    def test_summary_page_gets_time_limit_data_for_problems_in_visible_statuses(self):
        for url in self.urls:
            self.login_as(self.provider)
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
        self.login_as(self.provider)
        resp = self.client.get(self.private_summary_url)
        self.assertContains(resp, 'Responded to', count=1, status_code=200)
        self.assertContains(resp, 'Unable to Resolve', count=1)
        self.assertContains(resp, 'Abusive/Vexatious', count=1)

    def test_summary_page_does_not_include_problems_in_hidden_statuses_in_total_row_summary_stats(self):
        for url in self.urls:
            self.login_as(self.provider)
            resp = self.client.get(url)
            summary_stats = resp.context['problems_summary_stats']
            self.assertEqual(summary_stats['happy_service'], 0.666666666666667)
            self.assertEqual(summary_stats['happy_outcome'], 1.0)
            self.assertEqual(summary_stats['average_time_to_acknowledge'], Decimal('6100.0000000000000000'))
            self.assertEqual(summary_stats['average_time_to_address'], Decimal('54300.0000000000000000000'))

    def test_summary_pages_display_summary_stats_values_in_visible_status_rows(self):
        for url in self.urls:
            self.login_as(self.provider)
            resp = self.client.get(url)
            self.assertContains(resp, '<td id="status_0_time_to_acknowledge">4 days</td>')
            self.assertContains(resp, '<td class="separator" id="status_0_time_to_address">38 days</td>')
            self.assertContains(resp, '<td id="status_0_happy_service">67%</td>')
            self.assertContains(resp, '<td id="status_0_happy_outcome">100%</td>')

    def test_private_summary_page_does_not_display_summary_stats_values_in_hidden_status_rows(self):
        self.login_as(self.provider)
        resp = self.client.get(self.private_summary_url)
        self.assertContains(resp, '<td id="status_7_time_to_acknowledge">—</td>')
        self.assertContains(resp, '<td class="separator" id="status_7_time_to_address">—</td>')
        self.assertContains(resp, '<td id="status_7_happy_service">—</td>')
        self.assertContains(resp, '<td id="status_7_happy_outcome">—</td>')

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

    def test_private_summary_page_is_inaccessible_to_other_providers(self):
        self.login_as(self.other_provider)
        resp = self.client.get(self.private_summary_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_summary_page_is_inaccessible_to_other_ccgs(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.private_summary_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_summary_page_is_accessible_to_pals_users(self):
        self.login_as(self.pals)
        resp = self.client.get(self.private_summary_url)
        self.assertEqual(resp.status_code, 200)


class OrganisationProblemsTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationProblemsTests, self).setUp()

        self.hospital = create_test_organisation({'organisation_type': 'hospitals',
                                                  'ods_code': 'ABC123'})
        self.gp_ccg = create_test_ccg({'code': 'MOO'})
        self.gp = create_test_organisation({'organisation_type': 'gppractices',
                                            'ods_code': 'DEF456'})
        self.gp.ccgs.add(self.gp_ccg)
        self.public_hospital_problems_url = reverse('public-org-problems',
                                                    kwargs={'ods_code': self.hospital.ods_code,
                                                            'cobrand': 'choices'})
        self.private_hospital_problems_url = reverse('private-org-problems',
                                                     kwargs={'ods_code': self.hospital.ods_code})
        self.public_gp_problems_url = reverse('public-org-problems',
                                              kwargs={'ods_code': self.gp.ods_code,
                                                      'cobrand': 'choices'})
        self.private_gp_problems_url = reverse('private-org-problems',
                                               kwargs={'ods_code': self.gp.ods_code})
        self.staff_problem = create_test_problem({'category': 'staff',
                                                  'organisation': self.hospital,
                                                  'moderated': Problem.MODERATED,
                                                  'publication_status': Problem.PUBLISHED,
                                                  'moderated_description': "Moderated description"})

        # Add some users to test access rights
        self.test_hospital_user = User.objects.create_user("Test hospital user", 'hospital@example.com', self.test_password)
        self.test_hospital_user.save()
        self.hospital.users.add(self.test_hospital_user)
        self.hospital.save()

        self.test_gp_user = User.objects.create_user("Test gp user", 'gp@example.com', self.test_password)
        self.test_gp_user.save()
        self.gp.users.add(self.test_gp_user)
        self.gp.save()

        # Add the pals user from AuthorizationTestCase to both hospital and gp
        self.hospital.users.add(self.pals)
        self.hospital.save()
        self.gp.users.add(self.pals)
        self.gp.save()

        # Add the CCG user from AuthorizationTestCase to the gp CCG
        self.gp_ccg.users.add(self.ccg_user)
        self.gp_ccg.save()

        # Add an explicitly public and an explicitly private problem to test
        # privacy is respected
        self.public_problem = create_test_problem({'organisation': self.hospital})
        self.private_problem = create_test_problem({'organisation': self.hospital, 'public': False})

    def test_shows_services_for_hospitals(self):
        for url in [self.public_hospital_problems_url, self.private_hospital_problems_url]:
            self.login_as(self.test_hospital_user)
            resp = self.client.get(url)
            self.assertContains(resp, '<th class="service">Department</th>', count=1, status_code=200)

    def test_shows_time_limits_for_hospitals(self):
        for url in [self.public_hospital_problems_url, self.private_hospital_problems_url]:
            self.login_as(self.test_hospital_user)
            resp = self.client.get(url)
            self.assertContains(resp, '<th class="time_to_acknowledge">Acknowledge</th>', count=1, status_code=200)
            self.assertContains(resp, '<th class="time_to_address">Address</th>', count=1, status_code=200)

    def test_no_services_for_gps(self):
        for url in [self.public_gp_problems_url, self.private_gp_problems_url]:
            self.login_as(self.test_gp_user)
            resp = self.client.get(url)
            self.assertNotContains(resp, '<th class="service">Department</th>')

    def test_no_time_limits_for_gps(self):
        for url in [self.public_gp_problems_url, self.private_gp_problems_url]:
            self.login_as(self.test_gp_user)
            resp = self.client.get(url)
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

    def test_public_page_shows_private_problems_without_links(self):
        # Add a private problem
        private_problem = create_test_problem({'organisation': self.hospital,
                                               'moderated': Problem.MODERATED,
                                               'publication_status': Problem.PUBLISHED,
                                               'public': False})
        private_problem_url = reverse('problem-view', kwargs={'pk': self.private_problem.id,
                                                              'cobrand': 'choices'})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertTrue(private_problem.reference_number in resp.content)
        self.assertTrue(private_problem.summary in resp.content)
        self.assertTrue(private_problem_url not in resp.content)

    def test_public_page_doesnt_show_hidden_or_unmoderated_problems(self):
        # Add some problems which shouldn't show up
        unmoderated_problem = create_test_problem({'organisation': self.hospital})
        unmoderated_problem_url = reverse('problem-view', kwargs={'pk': unmoderated_problem.id,
                                                                  'cobrand': 'choices'})
        hidden_problem = create_test_problem({'organisation': self.hospital,
                                              'moderated': Problem.MODERATED,
                                              'publication_status': Problem.HIDDEN})
        hidden_problem_url = reverse('problem-view', kwargs={'pk': hidden_problem.id,
                                                             'cobrand': 'choices'})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertTrue(unmoderated_problem_url not in resp.content)
        self.assertTrue(hidden_problem_url not in resp.content)

    def test_private_page_exists(self):
        self.login_as(self.test_hospital_user)
        resp = self.client.get(self.private_hospital_problems_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_page_links_to_problems(self):
        self.login_as(self.test_hospital_user)
        response_url = reverse('response-form', kwargs={'pk': self.staff_problem.id})
        resp = self.client.get(self.private_hospital_problems_url)
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
        self.login_as(self.test_hospital_user)
        resp = self.client.get(self.private_hospital_problems_url)
        self.assertTrue(unmoderated_response_url in resp.content)
        self.assertTrue(hidden_response_url in resp.content)
        self.assertTrue(private_response_url in resp.content)
        self.assertTrue(private_problem.private_summary in resp.content)

    def test_private_page_is_inaccessible_to_anon_users(self):
        expected_login_url = "{0}?next={1}".format(self.login_url, self.private_hospital_problems_url)
        resp = self.client.get(self.private_hospital_problems_url)
        self.assertRedirects(resp, expected_login_url)

    def test_private_pages_are_accessible_to_all_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.private_hospital_problems_url)
            self.assertEqual(resp.status_code, 200)
            resp = self.client.get(self.private_gp_problems_url)
            self.assertEqual(resp.status_code, 200)

    def test_private_pages_are_accessible_to_pals_users(self):
        self.login_as(self.pals)
        resp = self.client.get(self.private_hospital_problems_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(self.private_gp_problems_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_page_is_inaccessible_to_other_providers(self):
        self.login_as(self.test_gp_user)
        resp = self.client.get(self.private_hospital_problems_url)
        self.assertEqual(resp.status_code, 403)
        self.login_as(self.test_hospital_user)
        resp = self.client.get(self.private_gp_problems_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_page_is_inaccessible_to_other_ccgs(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.private_hospital_problems_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_page_is_accessible_to_ccg(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.private_gp_problems_url)
        self.assertEqual(resp.status_code, 200)

    def test_filters_by_status(self):
        # Add a problem in a different status that would show up
        resolved_problem = create_test_problem({'organisation': self.hospital,
                                                'status': Problem.ACKNOWLEDGED,
                                                'moderated': Problem.MODERATED,
                                                'publication_status': Problem.PUBLISHED,
                                                'moderated_description': 'Moderated'})
        status_filtered_url = "{0}?status={1}".format(self.public_hospital_problems_url, Problem.NEW)
        resp = self.client.get(status_filtered_url)
        self.assertContains(resp, self.staff_problem.reference_number)
        self.assertNotContains(resp, resolved_problem.reference_number)

    def shows_all_statuses_on_private_page(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.private_hospital_problems_url)
        for status, label in Problem.STATUS_CHOICES:
            self.assertContains(resp, '<option value={0}>{1}</option>'.format(status, label))

    def shows_only_public_statuses_on_public_page(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.private_hospital_problems_url)
        for status, label in Problem.STATUS_CHOICES:
            if status in Problem.HIDDEN_STATUSES:
                self.assertNotContains(resp, '<option value={0}>{1}</option>'.format(status, label))

    def ignores_private_statuses_on_public_page(self):
        # Even if we manually hack the url, it shouldn't do any filtering
        # Add a problem in a different status that would show up
        abusive_problem = create_test_problem({'organisation': self.hospital,
                                               'status': Problem.ABUSIVE,
                                               'moderated': Problem.MODERATED,
                                               'publication_status': Problem.PUBLISHED,
                                               'moderated_description': 'Moderated'})
        status_filtered_url = "{0}?status={1}".format(self.public_hospital_problems_url, Problem.ABUSIVE)
        resp = self.client.get(status_filtered_url)
        self.assertContains(resp, self.staff_problem.reference_number)
        # The default status option should still be selected, not any other
        self.assertContains(resp, '<option value="" selected="selected">Problem status</option>')
        self.assertNotContains(resp, abusive_problem.reference_number)

    def test_filters_by_category(self):
        # Add a problem in a different status that would show up
        cleanliness_problem = create_test_problem({'organisation': self.hospital,
                                                   'category': 'cleanliness',
                                                   'moderated': Problem.MODERATED,
                                                   'publication_status': Problem.PUBLISHED,
                                                   'moderated_description': 'Moderated'})
        category_filtered_url = "{0}?category=cleanliness".format(self.public_hospital_problems_url)
        resp = self.client.get(category_filtered_url)
        self.assertContains(resp, cleanliness_problem.reference_number)
        self.assertNotContains(resp, self.staff_problem.reference_number)

    def test_private_page_filters_by_breach(self):
        # Add a breach problem
        self.login_as(self.test_hospital_user)
        breach_problem = create_test_problem({'organisation': self.hospital,
                                              'breach': True,
                                              'moderated': Problem.MODERATED,
                                              'publication_status': Problem.PUBLISHED,
                                              'moderated_description': 'Moderated'})
        breach_filtered_url = "{0}?breach=True".format(self.private_hospital_problems_url)
        resp = self.client.get(breach_filtered_url)
        self.assertContains(resp, breach_problem.reference_number)
        self.assertNotContains(resp, self.staff_problem.reference_number)

    def test_public_page_does_not_have_breach_filter(self):
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, '<select name="breach" id="id_breach">')

    def test_doesnt_show_service_for_gp(self):
        resp = self.client.get(self.public_gp_problems_url)
        self.assertNotContains(resp, '<select name="service_id" id="id_service_id">')

    def test_filters_by_service_for_hospital(self):
        # Add a service to the test hospital
        service = create_test_service({'organisation': self.hospital})
        # Add a problem about a specific service
        service_problem = create_test_problem({'organisation': self.hospital,
                                               'service': service,
                                               'moderated': Problem.MODERATED,
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

    def test_private_page_highlights_priority_problems(self):
        # Add a priority problem
        self.login_as(self.test_hospital_user)
        create_test_problem({'organisation': self.hospital,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'priority': Problem.PRIORITY_HIGH})
        resp = self.client.get(self.private_hospital_problems_url)
        self.assertContains(resp, 'problem-table__highlight')

    def test_public_page_doesnt_highlight_priority_problems(self):
        # Add a priority problem
        create_test_problem({'organisation': self.hospital,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'priority': Problem.PRIORITY_HIGH})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, 'problem-table__highlight')

    def test_private_page_shows_breach_flag(self):
        self.login_as(self.test_hospital_user)
        create_test_problem({'organisation': self.hospital,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'breach': True})
        resp = self.client.get(self.private_hospital_problems_url)
        self.assertContains(resp, '<div class="problem-table__flag__breach">b</div>')

    def test_public_page_doesnt_show_breach_flag(self):
        create_test_problem({'organisation': self.hospital,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'breach': True})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, '<div class="problem-table__flag__breach">b</div>')

    def test_private_page_shows_escalated_flag(self):
        self.login_as(self.test_hospital_user)
        create_test_problem({'organisation': self.hospital,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'status': Problem.ESCALATED,
                             'commissioned': Problem.LOCALLY_COMMISSIONED})
        resp = self.client.get(self.private_hospital_problems_url)
        self.assertContains(resp, '<div class="problem-table__flag__escalate">e</div>')

    def test_public_page_doesnt_show_escalated_flag(self):
        create_test_problem({'organisation': self.hospital,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'status': Problem.ESCALATED,
                             'commissioned': Problem.LOCALLY_COMMISSIONED})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, '<div class="problem-table__flag__escalate">e</div>')

    def test_private_page_shows_private_summary(self):
        self.login_as(self.test_hospital_user)
        create_test_problem({'organisation': self.hospital,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'description': 'private description',
                             'moderated_description': 'public description'})
        resp = self.client.get(self.private_hospital_problems_url)
        self.assertContains(resp, 'private description')
        self.assertNotContains(resp, 'public description')

    def test_public_page_shows_public_summary(self):
        create_test_problem({'organisation': self.hospital,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'description': 'private description',
                             'moderated_description': 'public description'})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, 'private description')
        self.assertContains(resp, 'public description')


class OrganisationDashboardTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationDashboardTests, self).setUp()
        self.problem = create_test_problem({'organisation': self.test_organisation})
        self.dashboard_url = reverse('org-dashboard', kwargs={'ods_code': self.test_organisation.ods_code})

    def test_dashboard_page_exists(self):
        self.login_as(self.provider)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_page_shows_organisation_name(self):
        self.login_as(self.provider)
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(self.test_organisation.name in resp.content)

    def test_dashboard_shows_problems(self):
        self.login_as(self.provider)
        response_url = reverse('response-form', kwargs={'pk': self.problem.id})
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(response_url in resp.content)

    def test_dashboard_doesnt_show_closed_problems(self):
        self.closed_problem = create_test_problem({'organisation': self.test_organisation,
                                                   'status': Problem.RESOLVED})
        closed_problem_response_url = reverse('response-form', kwargs={'pk': self.closed_problem.id})
        self.login_as(self.provider)
        resp = self.client.get(self.dashboard_url)
        self.assertTrue(closed_problem_response_url not in resp.content)

    def test_dashboard_doesnt_show_escalated_problems(self):
        self.escalated_problem = create_test_problem({'organisation': self.test_organisation,
                                                      'status': Problem.ESCALATED,
                                                      'commissioned': Problem.LOCALLY_COMMISSIONED})
        escalated_problem_response_url = reverse('response-form', kwargs={'pk': self.escalated_problem.id})
        self.login_as(self.provider)
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

    def test_dashboard_page_is_inaccessible_to_other_providers(self):
        self.login_as(self.other_provider)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 403)

    def test_dashboard_page_is_inaccessible_to_other_ccgs(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 403)

    def test_dashboard_page_highlights_priority_problems(self):
        # Add a priority problem
        self.login_as(self.provider)
        create_test_problem({'organisation': self.test_organisation,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'priority': Problem.PRIORITY_HIGH})
        resp = self.client.get(self.dashboard_url)
        self.assertContains(resp, 'problem-table__highlight')

    def test_dashboard_page_shows_breach_flag(self):
        self.login_as(self.provider)
        create_test_problem({'organisation': self.test_organisation,
                             'moderated': Problem.MODERATED,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'breach': True})
        resp = self.client.get(self.dashboard_url)
        self.assertContains(resp, '<div class="problem-table__flag__breach">b</div>')


class OrganisationMapTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationMapTests, self).setUp()
        self.hospital = self.test_organisation
        self.other_gp = self.other_test_organisation
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

    def test_public_map_doesnt_include_unmoderated_or_unpublished_or_hidden_status_problems(self):
        create_test_problem({'organisation': self.other_gp})
        create_test_problem({'organisation': self.other_gp,
                             'publication_status': Problem.HIDDEN,
                             'moderated': Problem.MODERATED})
        create_test_problem({'organisation': self.other_gp,
                             'publication_status': Problem.PUBLISHED,
                             'moderated': Problem.MODERATED,
                             'status': Problem.ABUSIVE})
        create_test_problem({'organisation': self.other_gp,
                            'publication_status': Problem.PUBLISHED,
                            'moderated': Problem.MODERATED})

        resp = self.client.get(self.map_url)
        response_json = json.loads(resp.context['organisations'])
        self.assertEqual(response_json[0]['all_time_open'], 1)

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
                             'moderated': Problem.MODERATED,
                             'category': 'staff'})
        create_test_problem({'organisation': self.other_gp,
                             'publication_status': Problem.PUBLISHED,
                             'moderated': Problem.MODERATED,
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
                             'moderated': Problem.MODERATED,
                             'status': Problem.NEW})
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'moderated': Problem.MODERATED,
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


@override_settings(SUMMARY_THRESHOLD=['all_time', 1])
class SummaryTests(AuthorizationTestCase):

    def setUp(self):
        super(SummaryTests, self).setUp()
        self.summary_url = reverse('org-all-summary', kwargs={'cobrand': 'choices'})
        create_test_problem({'organisation': self.test_organisation, 'category': 'staff'})
        create_test_problem({'organisation': self.other_test_organisation,
                             'publication_status': Problem.PUBLISHED,
                             'moderated': Problem.MODERATED,
                             'status': Problem.ABUSIVE,
                             'category': 'cleanliness'})

    def test_summary_page_exists(self):
        resp = self.client.get(self.summary_url)
        self.assertEqual(resp.status_code, 200)

    def test_summary_doesnt_include_hidden_status_problems_in_default_view(self):
        resp = self.client.get(self.summary_url)
        self.assertContains(resp, 'Test Organisation')
        self.assertNotContains(resp, 'Other Test Organisation')
        self.assertContains(resp, '<td class="all_time">1</td>', count=1, status_code=200)

    def test_status_filter_only_shows_visible_statuses_in_filters(self):
        resp = self.client.get(self.summary_url)
        for status in Problem.HIDDEN_STATUSES:
            self.assertNotContains(resp, Problem.STATUS_CHOICES[status][1])

    def test_summary_page_ignores_hidden_status_filter(self):
        resp = self.client.get(self.summary_url + '?status={0}'.format(Problem.ABUSIVE))
        self.assertContains(resp, 'Test Organisation')
        self.assertNotContains(resp, 'Other Test Organisation')
        self.assertContains(resp, '<td class="all_time">1</td>', count=1, status_code=200)

    def test_summary_page_applies_threshold_from_settings(self):
        with self.settings(SUMMARY_THRESHOLD=('six_months', 1)):
            resp = self.client.get(self.summary_url)
            self.assertContains(resp, 'Test Organisation')

        with self.settings(SUMMARY_THRESHOLD=('six_months', 2)):
            resp = self.client.get(self.summary_url)
            self.assertNotContains(resp, 'Test Organisation')

    def test_summary_page_filters_by_ccg(self):
        # Add an issue for other_test_organisation that won't be filtered because
        # of it's Hidden status bit will be by the other orgs ccg
        create_test_problem({'organisation': self.other_test_organisation})

        ccg_filtered_url = '{0}?ccg={1}'.format(self.summary_url, self.test_ccg.id)
        resp = self.client.get(ccg_filtered_url)
        self.assertContains(resp, self.test_organisation.name)
        self.assertNotContains(resp, self.other_test_organisation.name)

    def test_summary_page_filters_by_organisation_type(self):
        # Add an issue for other_test_organisation that won't be filtered because
        # of it's Hidden status but will be by the org_type filter
        create_test_problem({'organisation': self.other_test_organisation})

        org_type_filtered_url = '{0}?organisation_type=hospitals'.format(self.summary_url)
        resp = self.client.get(org_type_filtered_url)
        self.assertContains(resp, self.test_organisation.name)
        self.assertNotContains(resp, self.other_test_organisation.name)

    def test_summary_page_filters_by_category(self):
        # Add an issue for other_test_organisation that won't be filtered because
        # of it's Hidden status but will be filtered by our category
        create_test_problem({'organisation': self.other_test_organisation,
                             'category': 'cleanliness'})

        category_filtered_url = '{0}?category=staff'.format(self.summary_url)
        resp = self.client.get(category_filtered_url)
        self.assertContains(resp, self.test_organisation.name)
        # NOTE: we rely on the SUMMARY_THRESHOLD setting to make this org disappear
        self.assertNotContains(resp, self.other_test_organisation.name)

    def test_summary_page_filters_by_status(self):
        # Add an issue for other_test_organisation that won't be filtered because
        # of it's Hidden status, but should be filtered by our status filter
        create_test_problem({'organisation': self.other_test_organisation,
                             'status': Problem.ACKNOWLEDGED})

        status_filtered_url = '{0}?status={1}'.format(self.summary_url, Problem.NEW)
        resp = self.client.get(status_filtered_url)
        self.assertContains(resp, self.test_organisation.name)
        # NOTE: we rely on the SUMMARY_THRESHOLD setting to make this org disappear
        self.assertNotContains(resp, self.other_test_organisation.name)

    def test_public_summary_page_does_not_have_breach_filter(self):
        resp = self.client.get(self.summary_url)
        self.assertNotContains(resp, '<select name="breach" id="id_breach">')


@override_settings(SUMMARY_THRESHOLD=None)
class PrivateNationalSummaryTests(AuthorizationTestCase):

    def setUp(self):
        super(PrivateNationalSummaryTests, self).setUp()
        self.summary_url = reverse('private-national-summary')
        create_test_problem({'organisation': self.test_organisation})
        create_test_problem({'organisation': self.other_test_organisation,
                             'publication_status': Problem.PUBLISHED,
                             'moderated': Problem.MODERATED,
                             'status': Problem.ABUSIVE})
        self.login_as(self.superuser)

    def test_summary_page_authorization(self):

        tests = (
            # (user, permitted? )
            ( None,                               False ),
            ( self.provider,                      False ),
            ( self.case_handler,                  False ),
            ( self.second_tier_moderator,         False ),

            ( self.superuser,                     True  ),
            ( self.nhs_superuser,                 True  ),
            ( self.customer_contact_centre_user,  True  ),

            # CCG users allowed, but only if they have CCGs attached to them.
            ( self.ccg_user,                      True  ),
            ( self.no_ccg_user,                   False ),
        )

        for user, permitted in tests:
            self.client.logout()
            if user:
                self.login_as(user)
            resp = self.client.get(self.summary_url)

            if permitted:
                self.assertEqual(resp.status_code, 200, "{0} should be allowed".format(user))
            elif user:  # trying to access and not logged in
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

    def test_ccg_user_only_sees_organisations_they_are_linked_to(self):

        # check that superuser sees both CCGs' organisations
        resp = self.client.get(self.summary_url)
        for org in self.test_ccg.organisations.all():
            self.assertContains(resp, org.name)
        for org in self.other_test_ccg.organisations.all():
            self.assertContains(resp, org.name)

        # change user
        self.client.logout()
        self.login_as(self.ccg_user)

        # check they see orgs for test_ccg and not for other_ccg
        resp = self.client.get(self.summary_url)
        for org in self.test_ccg.organisations.all():
            self.assertContains(resp, org.name)
        for org in self.other_test_ccg.organisations.all():
            self.assertNotContains(resp, org.name)

    def test_ccg_user_with_multiple_ccgs_can_still_use_ccg_filter_to_only_view_orgs_for_one(self):
        # Add ccg user to other_test_ccg as well
        self.other_test_ccg.users.add(self.ccg_user)
        self.other_test_ccg.save()
        # Login
        self.client.logout()
        self.login_as(self.ccg_user)

        # Check see both
        resp = self.client.get(self.summary_url)
        for org in self.test_ccg.organisations.all():
            self.assertContains(resp, org.name)
        for org in self.other_test_ccg.organisations.all():
            self.assertContains(resp, org.name)

        # Apply CCG filter
        resp = self.client.get("{0}?ccg={1}".format(self.summary_url, self.test_ccg.id))

        # Check filter applied
        for org in self.test_ccg.organisations.all():
            self.assertContains(resp, org.name)
        for org in self.other_test_ccg.organisations.all():
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
        create_test_problem({'organisation': self.test_organisation,
                             'breach': True})

        breach_filtered_url = '{0}?breach=True'.format(self.summary_url)
        resp = self.client.get(breach_filtered_url)
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

    def test_results_page_shows_paginator_for_over_ten_results(self):
        for i in range(12):
            create_test_organisation({
                'name': 'Multi GP',
                'organisation_type': 'gppractices',
                'ods_code': 'ABC{0}'.format(i)
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

    def test_dashboard_accessible_to_customer_contact_centre(self):
        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_shows_all_problems_for_nhs_superusers(self):
        self.login_as(self.nhs_superuser)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, self.org_local_escalated_problem.reference_number)
        self.assertContains(resp, self.org_national_escalated_problem.reference_number)
        self.assertContains(resp, self.org_local_escalated_acknowledged_problem.reference_number)
        self.assertContains(resp, self.other_org_local_escalated_problem.reference_number)
        self.assertContains(resp, self.other_org_national_escalated_problem.reference_number)

    def test_dashboard_doesnt_show_escalated_resolved_problem(self):
        self.login_as(self.nhs_superuser)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertNotContains(resp, self.org_local_escalated_resolved_problem.reference_number)

    def test_dashboard_only_shows_locally_commissioned_problems_to_escalation_ccg_organisations(self):
        self.login_as(self.ccg_user)
        # Remove the test ccg from the ccgs for this org so that we know access is coming
        # via the escalation_ccg field, not the ccgs association
        self.test_organisation.ccgs.remove(self.test_ccg)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, self.org_local_escalated_problem.reference_number)
        # Does not show other org's problem or nationally commmissioned problem for this org
        self.assertNotContains(resp, self.org_national_escalated_problem.reference_number)
        self.assertNotContains(resp, self.other_org_local_escalated_problem.reference_number)
        self.assertNotContains(resp, self.other_org_national_escalated_problem.reference_number)

    def test_dashboard_only_shows_nationally_commissioned_problems_to_customer_care_centre(self):
        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.escalation_dashboard_url)
        # Shows nationally commissioned problems for all orgs
        self.assertContains(resp, self.org_national_escalated_problem.reference_number)
        self.assertContains(resp, self.other_org_national_escalated_problem.reference_number)
        # Does not show locally commissioned problems
        self.assertNotContains(resp, self.org_local_escalated_problem.reference_number)
        self.assertNotContains(resp, self.other_org_local_escalated_problem.reference_number)

    def test_dashboard_hides_ccg_filter_only_for_ccg_users(self):
        # CCG users are by-default filtered to their ccg only, so no need
        # for the filter
        ccg_filter_to_look_for = 'name="ccg"'

        self.login_as(self.ccg_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertNotContains(resp, ccg_filter_to_look_for)

        self.login_as(self.nhs_superuser)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, ccg_filter_to_look_for)

        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.escalation_dashboard_url)
        self.assertContains(resp, ccg_filter_to_look_for)

    def test_dashboard_hides_status_filter(self):
        status_filter_to_look_for = 'name="status"'

        self.login_as(self.ccg_user)
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
        # self.test_organisation is a hospital, self.test_other_organisation is a GP
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
        breach_filtered_url = '{0}?breach=True'.format(self.escalation_dashboard_url)

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


class BreachDashboardTests(AuthorizationTestCase):

    def setUp(self):
        super(BreachDashboardTests, self).setUp()
        self.breach_dashboard_url = reverse('escalation-breaches')
        self.org_breach_problem = create_test_problem({'organisation': self.test_organisation,
                                                       'breach': True})
        self.other_org_breach_problem = create_test_problem({'organisation': self.other_test_organisation,
                                                             'breach': True})
        self.org_problem = create_test_problem({'organisation': self.test_organisation})

    def test_dashboard_accessible_to_ccg_users(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.breach_dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_accessible_to_customer_contact_centre(self):
        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.breach_dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_is_inacessible_to_anyone_else(self):
        people_who_shouldnt_have_access = [
            self.provider,
            self.no_provider,
            self.other_provider,
            self.pals,
            self.second_tier_moderator
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

    def test_dashboard_limits_problems_to_ccg_for_ccg_users(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.breach_dashboard_url)
        self.assertContains(resp, self.org_breach_problem.reference_number)
        self.assertNotContains(resp, self.other_org_breach_problem.reference_number)

    def test_dashboard_shows_all_breaches_to_superusers_and_customer_contact_centre(self):
        for user in (self.customer_contact_centre_user, self.nhs_superuser):
            self.login_as(user)
            resp = self.client.get(self.breach_dashboard_url)
            self.assertContains(resp, self.org_breach_problem.reference_number)
            self.assertContains(resp, self.other_org_breach_problem.reference_number)

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
