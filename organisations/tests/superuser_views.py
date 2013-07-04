# encoding: utf-8
# Django imports
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

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
            (self.customer_contact_centre_user,  False),

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
