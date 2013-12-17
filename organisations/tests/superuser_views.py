# encoding: utf-8
import csv
from StringIO import StringIO

# Django imports
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.test.utils import override_settings

# App imports
from issues.models import Problem

from .lib import create_test_problem, AuthorizationTestCase


@override_settings(SUMMARY_THRESHOLD=None)
class SuperuserDashboardTests(AuthorizationTestCase):

    def setUp(self):
        super(SuperuserDashboardTests, self).setUp()
        self.dashboard_url = reverse('superuser-dashboard')
        create_test_problem({'organisation': self.test_hospital})
        create_test_problem({'organisation': self.test_gp_branch,
                             'publication_status': Problem.PUBLISHED,
                             'status': Problem.ABUSIVE})
        self.login_as(self.superuser)

    def test_dashboard_page_authorization(self):

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
        )

        for user, permitted in tests:
            self.client.logout()
            if user:
                self.login_as(user)
            resp = self.client.get(self.dashboard_url)

            if permitted:
                self.assertEqual(resp.status_code, 200, "{0} should be allowed".format(user))
            elif user:  # trying to access and logged in
                self.assertEqual(resp.status_code, 403, "{0} should be denied".format(user))
            else:  # trying to access and not logged in
                expected_redirect_url = "{0}?next={1}".format(reverse("login"), self.dashboard_url)
                self.assertRedirects(resp, expected_redirect_url, msg_prefix="{0} should not be allowed".format(user))

    def test_dashboard_page_exists(self):
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_page_shows_ccgs(self):
        resp = self.client.get(self.dashboard_url)
        for ccg in [self.test_ccg, self.other_test_ccg]:
            expected_ccg_link = reverse('ccg-dashboard', kwargs={'code': ccg.code})
            self.assertContains(resp, expected_ccg_link)
            self.assertContains(resp, ccg.name)

    def test_dashboard_page_shows_organisation_parents(self):
        resp = self.client.get(self.dashboard_url)
        for parent in [self.test_trust, self.test_gp_surgery]:
            expected_parent_link = reverse('org-parent-dashboard', kwargs={'code': parent.code})
            self.assertContains(resp, expected_parent_link)
            self.assertContains(resp, parent.name)

    def test_dashboard_page_shows_link_to_logs(self):
        resp = self.client.get(self.dashboard_url)
        expected_logs_link = reverse('superuser-logs')
        self.assertContains(resp, expected_logs_link)

    def test_dashboard_page_shows_link_to_problems_csv(self):
        resp = self.client.get(self.dashboard_url)
        expected_csv_link = reverse('problems-csv')
        self.assertContains(resp, expected_csv_link)

class ProblemsCSVTests(AuthorizationTestCase):

    def setUp(self):
        super(ProblemsCSVTests, self).setUp()

        self.download_url = reverse("problems-csv")

        self.test_problem = create_test_problem({'organisation': self.test_hospital})

        self.test_closed_problem = create_test_problem({
            'organisation': self.test_hospital,
            'status': Problem.RESOLVED,
            'resolved': timezone.now(),
            'moderated_description': 'moderated',
            'publication_status': Problem.PUBLISHED,
            'commissioned': Problem.LOCALLY_COMMISSIONED,
            'time_to_acknowledge': 120 + 8, # 2 hours, 8 mins
            'time_to_address': 1440 + 60 + 15, # 1 day, 1 hour, 15 mins
            'survey_sent': timezone.now(),
            'happy_service': True,
            'happy_outcome': False
        })

    def test_csv_download_page_exists(self):
        self.login_as(self.superuser)
        resp = self.client.get(self.download_url)
        self.assertEqual(resp.status_code, 200)
        reader = csv.reader(StringIO(resp.content))
        expected_rows = [
            [
                'ID',
                'Organisation',
                'Service',
                'Created',
                'Status',
                'Privacy', # Public and Public Reporter name in one field
                'Category',
                'Original Description',
                'Moderated Description',
                'Reporter Name',
                'Reporter Email',
                'Reporter Phone',
                'Preferred Contact Method',
                'Source',
                'Website', # cobrand in the model
                'Published', # publication_status in the model
                'Priority',
                'Under 16',
                'Breach',
                'Commissioned',
                'Formal Complaint',
                'Time to Acknowledge',
                'Time to Address',
                'Last Modified',
                'Resolved',
                'Survey Sent',
                'Happy with Service',
                'Happy with Outcome',
            ],
            [
                str(self.test_problem.id),
                'Test Organisation',
                '',
                self.test_problem.created.strftime('%d/%m/%Y %H:%M'),
                'Open',
                'Public with reporter name',
                'Staff Attitude',
                'A test problem',
                '',
                'Test User',
                'reporter@example.com',
                '',
                'email',
                '',
                'choices',
                'Not moderated',
                'High',
                'False',
                'False',
                '',
                'False',
                '',
                '',
                self.test_problem.modified.strftime('%d/%m/%Y %H:%M'),
                '',
                '',
                '',
                ''
            ],
            [
                str(self.test_closed_problem.id),
                'Test Organisation',
                '',
                self.test_closed_problem.created.strftime('%d/%m/%Y %H:%M'),
                'Closed',
                'Public with reporter name',
                'Staff Attitude',
                'A test problem',
                'moderated',
                'Test User',
                'reporter@example.com',
                '',
                'email',
                '',
                'choices',
                'Published',
                'High',
                'False',
                'False',
                'Locally Commissioned',
                'False',
                '2 hours, 8 minutes',
                '1 day, 1 hour, 15 minutes',
                self.test_closed_problem.modified.strftime('%d/%m/%Y %H:%M'),
                self.test_closed_problem.resolved.strftime('%d/%m/%Y %H:%M'),
                self.test_closed_problem.survey_sent.strftime('%d/%m/%Y %H:%M'),
                'True',
                'False'
            ]
        ]
        for row, expected_row in zip(reader, expected_rows):
            self.assertEqual(row, expected_row)
